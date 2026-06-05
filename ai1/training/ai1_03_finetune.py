"""
AI1-03 | ThreadLearn — Fine-tune Qwen2.5-Coder-1.5B (QLoRA)
Dành cho SFTTrainer sử dụng tập dữ liệu threadlearn_train.jsonl
Tương thích với trl >= 1.5.0
"""
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig

# 1. Configs
MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B"
TRAIN_DATA = "threadlearn_train.jsonl"
EVAL_DATA = "threadlearn_train_eval.jsonl"
OUTPUT_DIR = "./threadlearn-qwen2.5-coder-1.5b"

def main():
    print("🚀 Khởi tạo quá trình Fine-tuning ThreadLearn với QLoRA...")

    # 2. Cấu hình Quantization (4-bit) để tiết kiệm VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16
    )

    # 3. Load Tokenizer & Model
    print(f"📥 Đang tải tokenizer và model từ HuggingFace ({MODEL_ID})...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # 4. Cấu hình LoRA (Theo chuẩn cho Qwen)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # Không wrap model bằng get_peft_model ở đây đối với trl>=0.12.0
    # SFTTrainer sẽ tự động xử lý.

    # 5. Load Dataset
    print("📦 Đang tải Dataset...")
    dataset = load_dataset("json", data_files={"train": TRAIN_DATA, "eval": EVAL_DATA})

    # Định dạng Prompt (Chuẩn mới của trl 1.5.0+)
    def formatting_prompts_func(example):
        return {"text": [f"{prompt}{completion}" for prompt, completion in zip(example['prompt'], example['completion'])]}

    print("📦 Đang map dataset...")
    dataset = dataset.map(formatting_prompts_func, batched=True)

    # 6. Training Arguments (Dùng SFTConfig)
    training_args = SFTConfig(
        dataset_text_field="text",
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=False,
        bf16=True, # Dùng bfloat16 nếu GPU hỗ trợ (Amphere+), nếu không chuyển thành fp16=True
        max_grad_norm=0.3,
        max_steps=500,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        eval_strategy="steps",
        eval_steps=50,
        report_to="none" # Đổi thành 'wandb' nếu bạn dùng Weights & Biases
    )

    # 7. Khởi tạo SFTTrainer
    print("🔥 Đang thiết lập SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["eval"],
        peft_config=lora_config,
        processing_class=tokenizer,
        args=training_args
    )

    # 8. Bắt đầu Train
    print("⚡ Bắt đầu huấn luyện...")
    trainer.train()

    # 9. Lưu Model
    print("💾 Đang lưu mô hình...")
    trainer.model.save_pretrained(f"{OUTPUT_DIR}/final_adapter")
    tokenizer.save_pretrained(f"{OUTPUT_DIR}/final_adapter")
    
    print("🎉 HOÀN TẤT! Mô hình đã được lưu tại thư mục:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
