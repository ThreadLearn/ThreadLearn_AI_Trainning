import json
import random
import os

random.seed(42)  # Cố định seed để có thể reproduce

def split_dataset(input_file, train_output, eval_output, split_ratio=0.9):
    if not os.path.exists(input_file):
        print(f"File không tồn tại: {input_file}")
        return

    # Load toàn bộ dữ liệu
    records = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Total samples in {os.path.basename(input_file)}: {len(records)}")

    # Xáo trộn dữ liệu
    random.shuffle(records)

    # Cắt 90/10
    split_index = int(len(records) * split_ratio)
    train_records = records[:split_index]
    eval_records = records[split_index:]

    # Ghi file Train
    with open(train_output, 'w', encoding='utf-8') as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # Ghi file Eval
    with open(eval_output, 'w', encoding='utf-8') as f:
        for r in eval_records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    print(f"Created Train set (90%): {os.path.basename(train_output)} with {len(train_records)} samples.")
    print(f"Created Eval set (10%): {os.path.basename(eval_output)} with {len(eval_records)} samples.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processed_dir = os.path.join(base_dir, 'processed')
    
    input_file = os.path.join(processed_dir, 'threadlearn_train_cot_master.jsonl')
    train_output = os.path.join(processed_dir, 'threadlearn_train_clean.jsonl')
    eval_output = os.path.join(processed_dir, 'threadlearn_eval_clean.jsonl')
    
    split_dataset(input_file, train_output, eval_output)
