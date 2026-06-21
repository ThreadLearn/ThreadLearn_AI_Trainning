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

def _mock_analyze(code: str, prompt: str) -> str:
    """
    Mock response — trả string code fix.
    """
    return "Promise.all([task1, task2]);"


# ---------------------------------------------------------------------------
# OpenAI client (AI2-08 — chưa implement)
# ---------------------------------------------------------------------------

def _openai_analyze(code: str, prompt: str) -> str:
    """
    [AI2-08] Gọi OpenAI GPT-3.5-turbo API.
    """
    if not OPENAI_API_KEY:
        return "Lỗi: Chưa cấu hình OPENAI_API_KEY trong file .env"
        
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
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Lỗi gọi OpenAI API: {e}")
        return f"// Lỗi API: {str(e)}\n{code}"


import json
import os
import urllib.request
import urllib.error
from config import OPENAI_API_KEY, HF_TOKEN
from output_parser import parse_model_output

# ---------------------------------------------------------------------------
# Hugging Face API client (Sử dụng Model vừa train)
# ---------------------------------------------------------------------------

def _hf_space_analyze(code: str, prompt: str) -> str:
    """
    [AI2-08] Gọi HuggingFace Space endpoint cho mô hình ThreadLearn vừa train.
    """
    # Nếu đang dùng Space API thì pass trực tiếp code để Space xử lý
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
            if issues:
                return issues[0].get("fix", code)
            return code
    except Exception as e:
        print(f"Lỗi gọi HF Space: {e}")
        return f"// Lỗi kết nối tới HF Space\n{code}"


# ---------------------------------------------------------------------------
# HF Inference API client — gọi fine-tuned model qua HF serverless GPU
# ---------------------------------------------------------------------------

def _local_with_hf_api_analyze(code: str, prompt: str) -> str:
    """
    Gọi HF Inference API (serverless) thay vì HF Space.
    """
    MODEL_ID = "anha12/threadlearn-qwen2.5-coder-1.5b-merged"
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

    if not HF_TOKEN:
        print("[hf_inference] HF_TOKEN not set — fallback to HF Space")
        return _hf_space_analyze(code, prompt)

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

            if isinstance(result, list) and result:
                raw_output = result[0].get("generated_text", "")
            elif isinstance(result, dict):
                if "error" in result:
                    wait = result.get("estimated_time", 20)
                    print(f"[hf_inference] Model loading, est. {wait}s — fallback to HF Space")
                    return _hf_space_analyze(code, prompt)
                raw_output = result.get("generated_text", "")
            else:
                raw_output = str(result)

            if not raw_output.strip():
                return _hf_space_analyze(code, prompt)

            return raw_output

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[hf_inference] HTTP {e.code}: {body[:200]}")
        return _hf_space_analyze(code, prompt)
    except Exception as e:
        print(f"[hf_inference] Error: {e}")
        return _hf_space_analyze(code, prompt)


# ---------------------------------------------------------------------------
# Public API — rag_pipeline.py gọi hàm này
# ---------------------------------------------------------------------------

def get_llm_fix(code: str, prompt: str) -> str:
    """
    Gọi LLM và trả về raw text do LLM sinh ra.
    """
    provider = LLM_PROVIDER.lower()

    if provider == "openai":
        return _openai_analyze(code, prompt)
    elif provider == "local_with_hf_api":
        return _local_with_hf_api_analyze(code, prompt)
    elif provider == "hf_space":
        return _hf_space_analyze(code, prompt)
    else:
        return _mock_analyze(code, prompt)
