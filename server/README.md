# ThreadLearn AI2 — Race Condition Detection Service

FastAPI microservice phát hiện race condition trong code JavaScript/TypeScript.  
Tích hợp BM25 RAG + LLM, trả kết quả qua REST API.

---

## Kiến trúc

```
Request → JWT Auth → Redis Cache (hit? return) → BM25 RAG → LLM → MongoDB History → Response
```

| Thành phần | Vai trò | Bắt buộc? |
|---|---|---|
| FastAPI server | Core API | ✅ |
| Redis | Cache kết quả analyze | Không (tắt thì bỏ qua cache) |
| MongoDB | Lưu lịch sử analyze | Không (tắt thì history trả rỗng) |
| LLM provider | Phân tích code thật | Không (dùng `mock` cho dev) |

---

## Yêu cầu

- Python 3.13+
- (Tùy chọn) Redis, MongoDB, Docker

---

## Chạy local (dev)

### Bước 1 — Cài dependencies

```bash
cd ThreadLearn-AI-Trainning/server/server
pip install -r requirements.txt
```

### Bước 2 — Tạo file `.env`

Tạo file `server/server/.env` với nội dung sau (copy và điền giá trị):

```env
# Chọn 1: mock | openai | ollama
# - mock   → dev/test, không cần key, trả Issue cứng
# - openai → cần OPENAI_API_KEY
# - ollama → cần Ollama chạy local
LLM_PROVIDER=mock

OPENAI_API_KEY=

# Phải khớp với JWT_SECRET trong Node.js backend
# Để trống hoặc giữ nguyên khi test local
JWT_SECRET=your_super_secret_access_key_change_me

# Tùy chọn — server chạy bình thường nếu thiếu
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
OLLAMA_URL=http://localhost:11434
HF_TOKEN=
```

> ⚠️ **Không commit file `.env` lên git.** File đã có trong `.gitignore`.

### Bước 3 — Chạy server

```bash
cd ThreadLearn-AI-Trainning/server/server
python -m uvicorn main:app --reload --port 8001
```

Kiểm tra server hoạt động:

```bash
curl http://localhost:8001/health
# → {"status":"ok","retriever_docs":2050}
```

Swagger UI: http://localhost:8001/docs

---

## Chạy với Docker

```bash
cd ThreadLearn-AI-Trainning/server

# Build image
docker build -t threadlearn-server .

# Chạy với env vars
docker run -d \
  -p 8001:8001 \
  -e LLM_PROVIDER=mock \
  -e JWT_SECRET=your_super_secret_access_key_change_me \
  --name server \
  threadlearn-server
```

Kiểm tra:

```bash
curl http://localhost:8001/health
```

---

## API Endpoints

### `GET /health` — Public, không cần token

```bash
curl http://localhost:8001/health
```

```json
{
  "status": "ok",
  "retriever_docs": 2050
}
```

---

### `POST /api/v1/ai/analyze` — Yêu cầu JWT

**Request:**

```bash
curl -X POST http://localhost:8001/api/v1/ai/analyze \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "for(var i=0;i<3;i++){setTimeout(function(){console.log(i)},1000);}",
    "language": "javascript",
    "user_id": "user-123"
  }'
```

**Response:**

```json
{
  "user_id": "user-123",
  "language": "javascript",
  "issues": [
    {
      "line_range": "1",
      "severity": "high",
      "description": "Closure loop variable — biến i dùng var, tất cả callback share cùng reference.",
      "fix": "Thay var bằng let để tạo block scope mới mỗi iteration."
    }
  ],
  "docs_used": ["Closure Loop Variable", "var vs let Scope"],
  "cached": false
}
```

| Field | Giá trị |
|---|---|
| `severity` | `"high"` / `"medium"` / `"low"` |
| `cached` | `true` nếu lấy từ Redis, `false` nếu gọi LLM mới |

---

### `GET /api/v1/ai/history/{user_id}` — Yêu cầu JWT

```bash
curl "http://localhost:8001/api/v1/ai/history/user-123?page=1&limit=20" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

```json
{
  "user_id": "user-123",
  "total": 5,
  "page": 1,
  "limit": 20,
  "records": [ ... ]
}
```

> Chỉ xem được history của chính mình — AI2 so sánh `user_id` trong JWT với param.

---

## Tích hợp từ Node.js Backend

### Tạo JWT

JWT phải được ký với cùng `JWT_SECRET` trong `server/server/.env`.

```javascript
import jwt from 'jsonwebtoken';

const token = jwt.sign(
  { sub: userId, exp: Math.floor(Date.now() / 1000) + 3600 },
  process.env.JWT_SECRET,
  { algorithm: 'HS256' }
);
```

### Gọi AI2

```javascript
const response = await fetch('http://localhost:8001/api/v1/ai/analyze', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code: userCode,
    language: 'javascript',
    user_id: userId,
  }),
});

const result = await response.json();
// result.issues[] — danh sách lỗi phát hiện được
```

---

## Chọn LLM Provider

| Provider | Cấu hình | Độ chính xác |
|---|---|---|
| `mock` | Không cần gì | Dev/demo only — trả Issue cứng |
| `openai` | `OPENAI_API_KEY=sk-...` | Cao nhất |
| `ollama` | Ollama chạy local + `OLLAMA_URL` | Trung bình, offline |

Đổi provider: sửa `LLM_PROVIDER` trong `server/server/.env` rồi restart server.

---

## Tích hợp Redis & MongoDB (tùy chọn)

Nếu không có, server vẫn chạy bình thường — chỉ mất cache và history.

**Chạy nhanh bằng Docker:**

```bash
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 27017:27017 mongo:7
```

---

## Chạy Tests

Từ thư mục gốc repo (`WDP-Code/`):

```bash
cd ThreadLearn-AI-Trainning/server/server
python -m pytest ../tests/ -v
```

---

## Giới hạn

| Giới hạn | Giá trị |
|---|---|
| Concurrent LLM calls | 3 (queue nếu vượt) |
| Timeout mỗi request | 30 giây |
| History per page | Tối đa 100 |
| Code input | 512 KB |
