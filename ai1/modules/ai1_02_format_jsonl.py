"""
AI1-02 | ThreadLearn — JSONL Formatter cho SFTTrainer
Chuyển đổi từ raw_dataset.json sang định dạng JSONL chuẩn bị cho fine-tune Qwen2.5-Coder-1.5B
"""

import json
import random
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Format dataset sang JSONL cho Qwen2.5-Coder")
    parser.add_argument("--input", default="raw_dataset.json", help="File JSON đầu vào")
    parser.add_argument("--output", default="threadlearn_train.jsonl", help="File JSONL đầu ra")
    parser.add_argument("--prompt-prefix", default="Convert to concurrent JavaScript:\n\n", help="Câu lệnh prompt trước input code")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Không tìm thấy file {args.input}")
        return

    # Load dataset
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"📦 Đã load {len(data)} mẫu từ {args.input}")

    # Lọc các mẫu hợp lệ (có đủ input/output)
    valid_data = [item for item in data if item.get("input") and item.get("output")]
    
    if len(valid_data) != len(data):
        print(f"⚠️ Đã loại bỏ {len(data) - len(valid_data)} mẫu không có input/output hợp lệ")

    # Shuffle dataset (Xáo trộn) để model học không bị bias theo thứ tự category
    random.seed(42) # Cố định seed để dễ tái hiện
    random.shuffle(valid_data)
    print("🔀 Đã xáo trộn ngẫu nhiên dữ liệu")

    # Format sang JSONL
    out_lines = []
    for item in valid_data:
        inp_code = item["input"].strip()
        out_code = item["output"].strip()
        
        # Định dạng chuẩn SFTTrainer
        jsonl_obj = {
            "prompt": f"{args.prompt_prefix}{inp_code}\n",
            "completion": f"{out_code}\n"
        }
        # Hoặc dùng định dạng ChatML (dành cho Qwen Chat, nhưng theo doc yêu cầu prompt-completion):
        # jsonl_obj = {
        #     "messages": [
        #         {"role": "user", "content": f"{args.prompt_prefix}{inp_code}"},
        #         {"role": "assistant", "content": out_code}
        #     ]
        # }
        
        out_lines.append(json.dumps(jsonl_obj, ensure_ascii=False))

    # Chia Train/Test split (90% - 10%)
    split_idx = int(len(out_lines) * 0.9)
    train_lines = out_lines[:split_idx]
    test_lines = out_lines[split_idx:]

    train_out = args.output
    test_out = args.output.replace(".jsonl", "_eval.jsonl")

    with open(train_out, "w", encoding="utf-8") as f:
        f.write("\n".join(train_lines) + "\n")
        
    with open(test_out, "w", encoding="utf-8") as f:
        f.write("\n".join(test_lines) + "\n")

    print("\n" + "━"*50)
    print("✅ ĐÃ CHUYỂN ĐỔI THÀNH CÔNG!")
    print(f"  • Train file : {train_out} ({len(train_lines)} mẫu)")
    print(f"  • Eval file  : {test_out} ({len(test_lines)} mẫu)")
    print("━"*50)
    print("Mẫu dữ liệu đầu tiên (Train):")
    first_sample = json.loads(train_lines[0])
    print(f"[PROMPT]:\n{first_sample['prompt'][:150]}...")
    print("-" * 20)
    print(f"[COMPLETION]:\n{first_sample['completion'][:150]}...")
    print("━"*50)
    print("\n🚀 BƯỚC TIẾP THEO: ")
    print("Bạn có thể đưa file threadlearn_train.jsonl này vào thư mục training của thư viện TRL / SFTTrainer để fine-tune Qwen2.5-Coder.")

if __name__ == "__main__":
    main()
