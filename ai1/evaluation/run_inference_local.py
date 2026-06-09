import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Đường dẫn mặc định khi lưu trên Kaggle
BASE_MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B"
# Đổi lại đường dẫn chính xác trỏ thẳng vào thư mục chứa adapter_config.json
ADAPTER_PATH = "./threadlearn-qwen2.5-coder-1.5b/final_adapter" # Hãy sửa nếu thư mục lưu của bạn khác tên này

test_cases = [
    {"id": "test_01", "category": "Race Condition", "code": "let counter = 0;\nfunction increment() {\n  setTimeout(() => {\n    counter++;\n  }, Math.random() * 100);\n}\nincrement(); increment();"},
    {"id": "test_02", "category": "Race Condition", "code": "const updateAccount = async (id, amount) => {\n  const balance = await db.getBalance(id);\n  setTimeout(() => db.setBalance(id, balance + amount), 10);\n};"},
    {"id": "test_06", "category": "Event Loop Blocking", "code": "function processHugeArray(arr) {\n  for(let i=0; i < arr.length; i++) {\n    heavyMath(arr[i]);\n  }\n}"},
    {"id": "test_11", "category": "Unhandled Rejection", "code": "app.get('/', (req, res) => {\n  db.query().then(data => res.json(data)); // Missing catch\n});"},
    {"id": "test_18", "category": "Missing Promise.all", "code": "async function sendEmails(users) {\n  for(let i=0; i<users.length; i++) {\n    await emailService.send(users[i].email);\n  }\n}"}
]

def main():
    print("📥 Đang tải Tokenizer và Base Model (Float16) từ HuggingFace...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID, 
        device_map="auto", 
        torch_dtype=torch.float16
    )

    print("🧠 Đang gắn bộ não LoRA (Adapter) mà bạn vừa train vào...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    
    print("\n🚀 Bắt đầu chấm điểm 5 bài thi khó nhất...\n")
    for idx, case in enumerate(test_cases):
        prompt = f"Convert to concurrent JavaScript:\n\n{case['code']}\n\n"
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        
        # Chạy inference
        outputs = model.generate(
            **inputs, 
            max_new_tokens=150, 
            temperature=0.2,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # Decode kết quả và cắt bỏ phần prompt ban đầu
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        fixed_code = result.replace(prompt, "").strip()
        
        print(f"✅ Case {idx+1} ({case['category']}):")
        print(fixed_code)
        print("-" * 50)

if __name__ == "__main__":
    main()
