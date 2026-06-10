import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from huggingface_hub import login
from kaggle_secrets import UserSecretsClient

def main():
    # 1. Khai báo thông tin
    BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B"
    ADAPTER_PATH = "./threadlearn-qwen2.5-coder-1.5b/final_adapter" 
    NEW_MODEL_NAME = "threadlearn-qwen2.5-coder-1.5b-merged"
    
    print("🔑 Đang đăng nhập Hugging Face...")
    try:
        user_secrets = UserSecretsClient()
        hf_token = user_secrets.get_secret("HF_TOKEN")
        login(token=hf_token)
    except Exception as e:
        print("Lưu ý: Nếu không dùng Kaggle Secrets, bạn có thể gõ trực tiếp token vào hàm login(token='...')")

    # 2. Tải Tokenizer và Base Model (Float16)
    # RẤT QUAN TRỌNG: Không được load 4-bit ở bước này, nếu không sẽ không Merge được!
    print(f"📥 Đang tải Base Model ({BASE_MODEL_ID}) vào RAM (Float16)...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        device_map="cpu", # Dùng CPU để tránh tràn VRAM khi merge nếu GPU Kaggle không đủ, hoặc auto
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True
    )

    # 3. Tải Adapter (Bộ não LoRA) và Gắn vào Base Model
    print(f"🧠 Đang tải Adapter từ {ADAPTER_PATH}...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

    # 4. Hợp nhất (Merge)
    print("🔥 Đang tiến hành Hợp nhất (Đun chảy LoRA vào Base Model)... Quá trình này có thể mất 1-2 phút.")
    merged_model = model.merge_and_unload()
    print("✅ Hợp nhất thành công!")

    # 5. Lưu xuống đĩa cứng (Tạo thành khối 3GB)
    print(f"💾 Đang lưu mô hình hoàn chỉnh ra thư mục ./{NEW_MODEL_NAME} ...")
    merged_model.save_pretrained(NEW_MODEL_NAME)
    tokenizer.save_pretrained(NEW_MODEL_NAME)

    # 6. Đẩy lên Hugging Face Hub
    print(f"☁️ Đang đẩy Cục 3GB này lên Hugging Face Hub... Có thể mất 5-10 phút tùy mạng.")
    merged_model.push_to_hub(NEW_MODEL_NAME)
    tokenizer.push_to_hub(NEW_MODEL_NAME)
    
    print("🎉 HOÀN TẤT TẤT CẢ! Mô hình độc lập đã nằm an toàn trên Hugging Face của bạn.")

if __name__ == "__main__":
    main()
