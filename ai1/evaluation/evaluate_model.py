import json
import urllib.request
import urllib.error
import time
import os

API_URL = "https://api-inference.huggingface.co/models/anha12/threadlearn-qwen2.5-coder-1.5b"
# Thay bằng token của bạn (có quyền Read) từ HuggingFace Settings -> Access Tokens
# Ví dụ: "Bearer hf_xxxxxxxxxxxxxxxxx"
HEADERS = {
    "Authorization": "Bearer <YOUR_HF_TOKEN_HERE>",
    "Content-Type": "application/json"
}

def query(payload):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(API_URL, data=data, headers=HEADERS, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        try:
            error_msg = json.loads(e.read().decode('utf-8'))
            return error_msg
        except:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🚀 Khởi chạy quá trình Inference qua Hugging Face API...")
    
    if "ĐIỀN_TOKEN" in HEADERS["Authorization"]:
        print("❌ LỖI: Bạn chưa điền Hugging Face Token vào biến HEADERS!")
        print("Vui lòng mở file evaluate_model.py và sửa lại dòng HEADERS.")
        return

    test_cases_path = "ai1/evaluation/test_cases.json"
    if not os.path.exists(test_cases_path):
        print(f"❌ Không tìm thấy file {test_cases_path}")
        return

    with open(test_cases_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"📦 Đã load {len(test_cases)} bài test. Bắt đầu chấm điểm...")
    results = []

    for idx, case in enumerate(test_cases):
        print(f"⏳ Đang xử lý Case {idx+1}/{len(test_cases)}: {case['category']}")
        prompt = f"Convert to concurrent JavaScript:\n\n{case['code']}"
        
        # Gọi Hugging Face Inference API
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 256,
                "temperature": 0.2,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        output = query(payload)
        
        # Xử lý kết quả trả về từ API
        generated_text = ""
        error_msg = None
        
        if isinstance(output, list) and len(output) > 0 and "generated_text" in output[0]:
            generated_text = output[0]["generated_text"].strip()
        elif isinstance(output, dict) and "error" in output:
            error_msg = output["error"]
            print(f"   ⚠️ Lỗi API: {error_msg}")
            
            # API HuggingFace thường cần thời gian "thức dậy" (Model Loading)
            if "loading" in error_msg.lower() or "estimated_time" in output:
                wait_time = output.get("estimated_time", 20)
                print(f"   💤 Model đang được load lên RAM của HF... Đợi {wait_time}s rồi thử lại.")
                time.sleep(wait_time)
                output = query(payload)
                if isinstance(output, list) and len(output) > 0 and "generated_text" in output[0]:
                    generated_text = output[0]["generated_text"].strip()
                    error_msg = None

        results.append({
            "id": case["id"],
            "category": case["category"],
            "prompt": case["code"],
            "model_output": generated_text,
            "error": error_msg
        })
        
        # Tránh bị Rate Limit
        time.sleep(1)

    # Lưu kết quả
    output_path = "ai1/evaluation/inference_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("━"*50)
    print(f"✅ ĐÃ HOÀN TẤT INFERENCE!")
    print(f"Kết quả đã được lưu tại: {output_path}")
    print("Bạn vui lòng gửi lại file này cho hệ thống để phân tích và ra Report nhé!")

if __name__ == "__main__":
    main()
