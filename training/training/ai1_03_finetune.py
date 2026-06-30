import os
import torch
from kaggle_secrets import UserSecretsClient
from huggingface_hub import login
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig
# ==========================================
# 1. XÁC THỰC HUGGING FACE & KAGGLE SECRETS
# ==========================================
user_secrets = UserSecretsClient()
hf_token = user_secrets.get_secret("HF_TOKEN")
login(token=hf_token)
print("✅ Đã kết nối Hugging Face thành công!")

# ==========================================
# 2. CẤU HÌNH ĐƯỜNG DẪN & THÔNG SỐ
# ==========================================
# Lưu ý: Sửa 'threadlearn-dataset' thành tên dataset thực tế của bạn trên Kaggle nếu có cảnh báo lỗi không tìm thấy file
DATA_PATH = "/kaggle/input/datasets/anhavan/threadlearn/threadlearn_train.jsonl"
OUTPUT_DIR = "./threadlearn-qwen2.5-coder-1.5b"
MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B"

def main():
    print("🚀 Khởi tạo quá trình Fine-tuning ThreadLearn với QLoRA...")

    # Cấu hình Quantization (4-bit) để không bị tràn VRAM Kaggle
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    print(f"📥 Đang tải tokenizer và model từ HuggingFace ({MODEL_ID})...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Cấu hình LoRA (Theo chuẩn cho mô hình Qwen)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    #model = get_peft_model(model, lora_config)
    #model.print_trainable_parameters()

        # Load Dataset từ Kaggle Path và chia 10% cho tập Đánh giá (Eval)
    print("📦 Đang tải Dataset...")
    dataset = load_dataset("json", data_files={"train": DATA_PATH})
    dataset = dataset["train"].train_test_split(test_size=0.1)

    # 1. SỬA HÀM FORMAT THÀNH DICT CHỨA KEY "text"
    def formatting_prompts_func(example):
        return {"text": [f"{prompt}{completion}" for prompt, completion in zip(example['prompt'], example['completion'])]}

    # 2. APPLY HÀM FORMAT VÀO DATASET TRƯỚC KHI TRAIN
    print("📦 Đang map dataset...")
    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 6. Training Arguments
    training_args = SFTConfig(
        dataset_text_field="text",  # <--- THÊM DÒNG NÀY ĐỂ BÁO CHO SFTTrainer BIẾT CỘT DATA LÀ "text"
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,      # Hạ xuống 1 để chống tràn RAM GPU T4
        per_device_eval_batch_size=1,       # <--- THÊM DÒNG NÀY (Chống sập lúc Evaluate)
        gradient_accumulation_steps=8,      # Tăng lên 8 để bù lại batch size
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=False,
        bf16=True, 
        max_grad_norm=0.3,
        max_steps=500,
        warmup_steps=15,
        lr_scheduler_type="cosine",
        eval_strategy="steps",
        eval_steps=50,
        report_to="none"
    )

    # 7. Khởi tạo SFTTrainer
    print("🔥 Đang thiết lập SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        peft_config=lora_config,
        # XÓA DÒNG formatting_func Ở ĐÂY
        processing_class=tokenizer, 
        args=training_args
    )
    # Bắt đầu Train
    print("⚡ Bắt đầu huấn luyện...")
    trainer.train()

    # Lưu Model cục bộ
    print("💾 Đang lưu mô hình...")
    trainer.model.save_pretrained(f"{OUTPUT_DIR}/final_adapter")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/final_adapter")
    
    # Đẩy thẳng lên Hugging Face Hub
    print("☁️ Đang đẩy model lên Hugging Face Hub...")
    trainer.push_to_hub("threadlearn-qwen2.5-coder-concurrency")
    
    print("🎉 HOÀN TẤT! Mô hình đã được lưu trên đám mây.")

if __name__ == "__main__":
    main()