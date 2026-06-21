"""
AI2-05: LLM Client — Mock implementation.
Trả hardcoded response để FE unblock ngay.

AI2-08: Swap sang OpenAI/Ollama thật mà không cần sửa rag_pipeline.py.
Strategy pattern: rag_pipeline chỉ gọi analyze_code(), không biết LLM là mock hay thật.
"""

from typing import List, Dict, Any

from config import LLM_PROVIDER
from schemas import Issue


# ---------------------------------------------------------------------------
# Mock LLM (dùng ngay bây giờ)
# ---------------------------------------------------------------------------

def _mock_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    Mock response — trả 1 issue cứng để FE có data test UI.
    Sẽ bị xóa khi AI2-08 hoàn thành.
    """
    return [
        Issue(
            line_range="1-10",
            severity="medium",
            description=(
                "[MOCK] Phát hiện khả năng race condition: "
                "biến shared có thể bị modify đồng thời bởi nhiều callback."
            ),
            fix=(
                "Dùng Promise.all() để kiểm soát luồng, "
                "hoặc Mutex/Semaphore nếu cần exclusive access."
            ),
        )
    ]


# ---------------------------------------------------------------------------
# OpenAI client (AI2-08 — chưa implement)
# ---------------------------------------------------------------------------

def _openai_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    [AI2-08] Gọi OpenAI GPT-3.5-turbo API.
    """
    if not OPENAI_API_KEY:
        return [Issue(
            line_range="all",
            severity="medium",
            description="Lỗi: Chưa cấu hình OPENAI_API_KEY trong file .env",
            fix="Hãy thêm OPENAI_API_KEY vào file .env"
        )]
        
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = (
        "Bạn là một chuyên gia sửa lỗi Node.js. "
        "Hãy tìm và sửa các lỗi bất đồng bộ (Race Condition, Event Loop Blocking) "
        "dựa trên code đầu vào. Vui lòng chỉ trả về mã nguồn đã sửa."
    )
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Convert to concurrent JavaScript:\n\n{code}"}
        ],
        "temperature": 0.2
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            raw_output = result["choices"][0]["message"]["content"]
            return parse_model_output(raw_output)
    except Exception as e:
        print(f"Lỗi gọi OpenAI API: {e}")
        return [Issue(
            line_range="all",
            severity="medium",
            description="Lỗi API khi gọi OpenAI",
            fix=f"Chi tiết: {str(e)}"
        )]


import json
import os
import urllib.request
import urllib.error
from config import OPENAI_API_KEY, HF_TOKEN
from output_parser import parse_model_output

# ---------------------------------------------------------------------------
# Hugging Face API client (Sử dụng Model vừa train)
# ---------------------------------------------------------------------------

def _ollama_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    [AI2-08] Gọi HuggingFace Space endpoint cho mô hình ThreadLearn vừa train.
    Space: https://anha12-threadlearn-ai2-api.hf.space
    """
    API_URL = "https://anha12-threadlearn-ai2-api.hf.space/analyze"

    payload = {
        "code": code,
        "language": "javascript",
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode('utf-8'))
            issues = result.get("issues", [])
            return [
                Issue(
                    line_range=iss.get("line_range", "all"),
                    severity=iss.get("severity", "medium"),
                    description=iss.get("description", ""),
                    fix=iss.get("fix", ""),
                    pattern_id=iss.get("pattern_id", "unknown"),
                )
                for iss in issues
            ]
    except Exception as e:
        print(f"Lỗi gọi HF Space: {e}")
        return [Issue(
            line_range="all",
            severity="medium",
            description="Lỗi kết nối tới HF Space",
            fix="Kiểm tra Space đang chạy tại https://huggingface.co/spaces/anha12/threadlearn-ai2-api",
        )]


# ---------------------------------------------------------------------------
# HF Inference API client — gọi fine-tuned model qua HF serverless GPU
# ---------------------------------------------------------------------------

def _hf_inference_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    Gọi HF Inference API (serverless) thay vì HF Space.
    - Chạy trên GPU shared của HF → ~2-4s thay vì 5-8s
    - Không cần manage Space, không cold start
    - Cần HF_TOKEN (Read access) trong .env
    """
    MODEL_ID = "anha12/threadlearn-qwen2.5-coder-1.5b-merged"
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

    if not HF_TOKEN:
        print("[hf_inference] HF_TOKEN not set — fallback to HF Space")
        return _ollama_analyze(code, context_docs)

    prompt = f"Convert to concurrent JavaScript:\n\n{code}"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "do_sample": False,
            "return_full_text": False,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_TOKEN}",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

            # HF Inference API trả list: [{"generated_text": "..."}]
            if isinstance(result, list) and result:
                raw_output = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                # Model đang load → {"error": "Model ... is currently loading"}
                if "error" in result:
                    wait = result.get("estimated_time", 20)
                    print(f"[hf_inference] Model loading, est. {wait}s — fallback to HF Space")
                    return _ollama_analyze(code, context_docs)
                raw_output = result.get("generated_text", "")
            else:
                raw_output = str(result)

            if not raw_output.strip():
                return _ollama_analyze(code, context_docs)

            return parse_model_output(raw_output)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[hf_inference] HTTP {e.code}: {body[:200]}")
        # 503 = model loading, fallback gracefully
        return _ollama_analyze(code, context_docs)
    except Exception as e:
        print(f"[hf_inference] Error: {e}")
        return _ollama_analyze(code, context_docs)


# ---------------------------------------------------------------------------
# Public API — rag_pipeline.py gọi hàm này
# ---------------------------------------------------------------------------

def analyze_code(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    Phân tích code và trả về danh sách Issue.

    Tự động chọn provider dựa trên LLM_PROVIDER trong .env:
        mock   → _mock_analyze()     ← mặc định hiện tại
        openai → _openai_analyze()   ← AI2-08
        ollama → _ollama_analyze()   ← AI2-08, blocked on AI1-07

    Args:
        code:         source code cần phân tích
        context_docs: top-3 docs từ BM25 search (đã có title + content)

    Returns:
        List[Issue] — rỗng nếu không phát hiện vấn đề
    """
    provider = LLM_PROVIDER.lower()

    if provider == "openai":
        return _openai_analyze(code, context_docs)
    elif provider == "hf_inference":
        return _hf_inference_analyze(code, context_docs)
    elif provider == "ollama":
        return _ollama_analyze(code, context_docs)
    else:
        # Mặc định: mock
        return _mock_analyze(code, context_docs)
