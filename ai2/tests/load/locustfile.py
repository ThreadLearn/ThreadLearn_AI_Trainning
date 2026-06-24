"""
AI2-10: Load test — ThreadLearn AI microservice.

Tool: Locust (pip install locust)
Chạy: locust -f ai2/tests/locustfile.py --host http://localhost:8001

Targets:
    10 concurrent users
    p50 < 8s, p95 < 15s
    0 crashes, 0 5xx errors (ngoại trừ 429 khi queue_full)

Cần set env:
    LOAD_TEST_JWT=<valid JWT token>   — hoặc sửa TOKEN bên dưới
"""

import os
from locust import HttpUser, task, between

# JWT hợp lệ — lấy từ Node.js backend hoặc tạo bằng helper trong test_main.py
TOKEN = os.getenv("LOAD_TEST_JWT", "SET_VALID_JWT_HERE")

SAMPLE_CODES = [
    # JS race condition — shared var + setTimeout
    """
let counter = 0;
for (let i = 0; i < 5; i++) {
    setTimeout(() => {
        counter++;
        console.log(counter);
    }, 100);
}
""",
    # JS Promise không await
    """
async function fetchData() {
    const result = fetch('/api/data');
    processResult(result);
}
""",
    # JS concurrent array write
    """
const results = [];
async function runAll(tasks) {
    tasks.forEach(async (t) => {
        const r = await processTask(t);
        results.push(r);
    });
}
""",
    # JS closure capturing var
    """
for (var i = 0; i < 3; i++) {
    setTimeout(function() {
        console.log(i);
    }, 1000);
}
""",
    # Clean code — no race condition
    """
async function safeFetch(url) {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (err) {
        console.error('Fetch failed:', err);
        return null;
    }
}
""",
]


class AIAnalyzeUser(HttpUser):
    """
    Simulates user sending code for analysis.
    wait_time: 1-3s between requests (realistic user pacing).
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Set auth header once per simulated user."""
        self.client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        self._code_index = 0

    @task(5)
    def analyze_code(self):
        """Main task: POST /api/v1/ai/analyze — weighted 5x."""
        code = SAMPLE_CODES[self._code_index % len(SAMPLE_CODES)]
        self._code_index += 1

        with self.client.post(
            "/api/v1/ai/analyze",
            json={
                "code": code,
                "language": "javascript",
                "user_id": "load-test-user",
            },
            catch_response=True,
            name="POST /analyze",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if "issues" not in data:
                    resp.failure("Response missing 'issues' field")
                else:
                    resp.success()
            elif resp.status_code == 429:
                # Queue full — expected under heavy load, không phải failure
                resp.success()
            elif resp.status_code == 504:
                resp.failure("LLM timeout (504)")
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def check_health(self):
        """Health check: GET /health — weighted 2x."""
        with self.client.get("/health", catch_response=True, name="GET /health") as resp:
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                resp.success()
            else:
                resp.failure(f"Health check failed: {resp.status_code}")

    @task(1)
    def get_history(self):
        """History: GET /history — weighted 1x."""
        with self.client.get(
            "/api/v1/ai/history/load-test-user",
            catch_response=True,
            name="GET /history",
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"History failed: {resp.status_code}")
