# Giải Thích Chi Tiết: PCWMs
## "Learning Reasoning World Models for Parallel Code"
**Singh et al. — arXiv 2604.20926v2, 2026**
**Lawrence Livermore National Laboratory + Northeastern University**

---

## 1. Bài Báo Này Giải Quyết Vấn Đề Gì?

### 1.1. Vấn Đề Gốc

LLM viết code serial (single-threaded) rất tốt — có hàng tỷ dòng code serial trên GitHub để train. Nhưng với **parallel code** (đa luồng, đồng thời) thì kém hơn nhiều.

Hai lý do:
1. **Thiếu dữ liệu training**: Code parallel phức tạp, ít được viết hơn
2. **Khó lý luận**: Thread interaction rất khó suy luận chỉ bằng đọc code — cần chạy và quan sát mới biết có race không

### 1.2. Cách Tiếp Cận Thông Thường và Vấn Đề

Giải pháp phổ biến: cho LLM gọi **tool bên ngoài** để kiểm tra code:

```
LLM viết code
    ↓
Gọi ThreadSanitizer (detect race) hoặc Caliper (đo performance)
    ↓
Nhận kết quả
    ↓
LLM sửa code dựa trên kết quả
```

**3 vấn đề với cách này**:
1. **Cấu hình tốn công**: ThreadSanitizer cần compile + link đặc biệt, Caliper cần instrument code
2. **Không dùng được cho code chưa hoàn chỉnh**: Phải compile được thì mới chạy tool được
3. **Chi phí cao**: Mỗi lần check phải build + run — chậm và tốn kém trong vòng lặp sửa code

### 1.3. Giải Pháp: Parallel-Code World Model (PCWM)

**Ý tưởng cốt lõi**: Thay vì gọi tool thật, hãy **dạy LLM tự mô phỏng tool** — nhìn code và tự suy luận kết quả mà không cần chạy gì.

```
Thông thường:
code → [compile + chạy ThreadSanitizer] → "có race tại dòng 14"
         (tốn 30-60 giây, cần môi trường build)

PCWM:
code → [LLM đọc và suy luận] → "có race tại dòng 14"
         (tốn < 1 giây, không cần build)
```

Đây gọi là **world model** — mô hình học cách mô phỏng môi trường (tool) thay vì tương tác trực tiếp.

---

## 2. World Model Là Gì? (Nền Tảng Lý Thuyết)

### 2.1. Khái Niệm Gốc

Trong AI và reinforcement learning, "world model" là mô hình học cách **dự đoán trạng thái tiếp theo của môi trường** — thay vì phải tương tác với môi trường thật (đắt, chậm, nguy hiểm), agent dùng world model để lên kế hoạch.

Ví dụ: Robot học đi không cần ngã thật → dùng world model để simulate rồi tìm cách giữ thăng bằng.

### 2.2. PCWM Cụ Thể

Với PCWM, "môi trường" = tool phân tích code. Định nghĩa hình thức:

```
z, y ← PCWM(x_code)
```

Trong đó:
- `x_code` = source code cần phân tích
- `z` = chuỗi suy luận (chain-of-thought reasoning trace)
- `y` = kết quả dự đoán (có race không? work percentage là bao nhiêu?)

**PCWM học**: Từ code → tự sinh chuỗi suy luận z → đưa ra kết quả y, mà không cần chạy tool thật.

### 2.3. Tại Sao Cần Chuỗi Suy Luận z?

Không thể chỉ học ánh xạ trực tiếp `code → kết quả` vì:
- Race condition phụ thuộc vào **nhiều yếu tố phức tạp** (thread scheduling, memory access pattern)
- Model cần **hiểu tại sao** mới dự đoán đúng các trường hợp mới
- Chuỗi suy luận giúp model **transfer** sang code chưa thấy bao giờ

---

## 3. Hai Tool Được PCWM Học Mô Phỏng

### 3.1. Tool 1: ThreadSanitizer (TSan)

**Mục đích**: Phát hiện **data race** — khi 2 thread cùng truy cập vùng nhớ, ít nhất 1 cái ghi, và không có synchronization.

**Cách hoạt động thật**: Runtime instrumentation — compile với `-fsanitize=thread`, chạy binary, TSan chèn check vào mọi memory access.

**Output ví dụ**:
```json
[
  {
    "type": "read/write race",
    "code_locations": ["generated.cc:14"]
  },
  {
    "type": "write/write race",
    "code_locations": ["generated.cc:14"]
  }
]
```

**Ví dụ code có race mà TSan sẽ detect**:
```cpp
// OpenMP parallel code — có data race
#include <omp.h>
double dotProduct = 0.0;

#pragma omp parallel for
for (int i = 0; i < n; i++) {
    dotProduct += a[i] * b[i];  // RACE: nhiều thread cùng đọc-ghi dotProduct
    //                              không có synchronization!
}
// Fix: dùng reduction clause
// #pragma omp parallel for reduction(+:dotProduct)
```

**PCWM học**: Nhìn code → nhận ra pattern `dotProduct +=` trong `omp parallel` → kết luận có race → output JSON như TSan.

### 3.2. Tool 2: Caliper

**Mục đích**: Profiling hiệu năng HPC — đo **work percentage** = tỷ lệ thời gian thread thực sự làm việc hữu ích (vs overhead: barrier wait, synchronization, idle time).

**Ý nghĩa work percentage**:
```
work% = 80% → thread dùng 80% thời gian tính toán, 20% chờ/overhead → TỐT
work% = 40% → thread chỉ 40% thời gian làm việc, 60% chờ → XẤU (lãng phí)
```

**Ví dụ cụ thể từ paper** (matrix multiply, OpenMP):
```
Thread count:    4    16    64    128
Work percentage: 96%  76%   44%   47%

→ 4 thread: gần lý tưởng (96% hiệu quả)
→ 64 thread: chỉ 44% — overhead (barrier sync, false sharing) chiếm 56%!
→ 128 thread không tệ hơn 64 nhiều vì đã hit bottleneck khác
```

**Task của PCWM Caliper**: Cho 2 đoạn code, dự đoán cái nào có **work percentage cao hơn** (pairwise comparison, không predict con số chính xác).

Ví dụ:
```cpp
// Code A — naive reduction
double sum = 0;
#pragma omp parallel for
for (int i = 0; i < n; i++) sum += arr[i];  // Race! Sai kết quả

// Code B — correct reduction  
double sum = 0;
#pragma omp parallel for reduction(+:sum)
for (int i = 0; i < n; i++) sum += arr[i];  // Đúng, OpenMP handles it

// PCWM Caliper: Code B có work% cao hơn Code A
// (Code A có race → undefined behavior → không thể profile đúng,
//  Code B dùng reduction → OpenMP tối ưu barrier tự động)
```

---

## 4. Kỹ Thuật Cốt Lõi: Hindsight Chain-of-Thought

Đây là **đóng góp quan trọng nhất của paper**. Để hiểu tại sao nó cần thiết, cần hiểu vấn đề khi dạy LLM suy luận về parallel code.

### 4.1. Cách Thông Thường: A Priori CoT (và Tại Sao Nó Thất Bại)

**A Priori CoT** = "Suy luận trước" = cho LLM tự suy luận → đoán kết quả:

```
Pipeline tạo training data với A Priori CoT:

1. Lấy code x_code
2. Hỏi LLM: "Code này có data race không? Hãy suy luận từng bước."
3. LLM sinh: reasoning_trace + prediction
4. Dùng (x_code, reasoning_trace, prediction) làm training sample
5. Fine-tune model khác trên dữ liệu này
```

**Vấn đề nghiêm trọng**: LLM đôi khi suy luận **sai** về thread interaction!

Race condition trong OpenMP code rất khó nhận ra chỉ bằng đọc — ngay cả human expert cũng khó. Khi LLM suy luận sai:
- Tạo ra reasoning trace sai (reasoning dẫn đến kết luận sai)
- Training trên reasoning sai → model học cách suy luận sai
- Model mới cũng suy luận sai → cascade failure

**Kết quả thực nghiệm**: Tất cả 4 model được train với A Priori CoT đều **collapse** về predict một label cố định:

```
Accuracy với A Priori CoT:
Qwen-2.5-32B: ~49%  ← đoán "có race" cho tất cả
Qwen-2.5-14B: ~49%  ← đoán "có race" cho tất cả
Qwen-2.5-7B:  ~49%  ← đoán "có race" cho tất cả
Llama-3.1-8B: ~49%  ← đoán "có race" cho tất cả

(Dataset balanced: ~49% "có race", ~51% "không có race")
→ Model học cách tốt nhất để minimize loss = đoán label phổ biến nhất
→ Hoàn toàn vô dụng!
```

**Tại sao collapse?** Khi training loss từ A Priori CoT:
```
Model suy luận sai → loss cao cho cả reasoning lẫn prediction
Model học: "để giảm loss prediction, đoán label phổ biến"
→ Prediction đúng hơn nhưng reasoning vô nghĩa
→ Vòng lặp tiêu cực: reasoning vô nghĩa → loss reasoning cao → model focus prediction hơn
→ Model chỉ predict label không cần reasoning → collapse
```

### 4.2. Giải Pháp: Hindsight CoT

**Ý tưởng**: Biết kết quả trước → mới viết reasoning dẫn đến kết quả đó.

```
Pipeline với Hindsight CoT:

1. Lấy code x_code
2. Chạy tool thật: y = ThreadSanitizer(x_code)  ← kết quả THẬT, CHẮC CHẮN ĐÚNG
3. Hỏi Teacher LLM: "Code này có kết quả y. Hãy phân tích từng bước 
   để cho thấy tại sao kết quả là y."
4. Teacher sinh: reasoning_trace (dẫn đến y một cách tự nhiên)
5. Training sample: (x_code, reasoning_trace, y)
6. Fine-tune Student LLM
```

**Tại sao Hindsight CoT không "gian lận"?**

Người ta có thể thắc mắc: "Nếu biết đáp án trước thì đâu có học được gì?"

Trả lời: Training data dùng (code, reasoning, answer) → model học **quy trình suy luận**, không học thuộc đáp án. Khi inference (không có answer), model áp dụng quy trình đó để tự suy luận.

Tương tự như học toán: xem đáp án giải từng bước → hiểu cách làm → tự làm bài tương tự mà không cần đáp án.

### 4.3. Constraint Quan Trọng: Causal Reasoning Forward

Prompt cho Teacher LLM **bắt buộc phải**:
- Suy luận **đi từ code → kết quả** (forward)
- **KHÔNG được** kiểu: "Vì tôi biết kết quả là X, nên..."
- LLM phải đóng vai người phân tích code, tự nhiên đi đến kết luận

**Ví dụ Hindsight CoT tốt** (cho code dot product bị race):
```
"Nhìn vào đoạn code này: mỗi thread thực hiện phép cộng tích lũy 
vào biến dotProduct. Biến này được khai báo ngoài vòng lặp parallel 
và tất cả thread đều đọc-ghi vào cùng địa chỉ memory.

Cụ thể, thao tác dotProduct += a[i] * b[i] gồm 3 bước:
1. Đọc giá trị hiện tại của dotProduct vào register
2. Tính a[i] * b[i] và cộng vào register
3. Ghi giá trị mới trở lại dotProduct

Nếu Thread 1 đang ở bước 1-2 và Thread 2 cũng đang ở bước 1-2 
đồng thời, cả hai đều đọc cùng giá trị dotProduct. Sau đó:
- Thread 1 ghi: dotProduct = cũ + contrib1
- Thread 2 ghi: dotProduct = cũ + contrib2  ← MẤT contrib1!

Không có #pragma omp reduction hay atomic nào được dùng.
→ Đây là read/write race tại biến dotProduct."
```

**Ví dụ Hindsight CoT XẤU** (vi phạm causal reasoning):
```
"Vì kết quả ThreadSanitizer cho thấy có race tại dòng 14, 
tôi nhìn vào dòng 14 và thấy... [giải thích ngược từ kết quả]"
→ KHÔNG DÙNG — model học backward reasoning, không transfer được
```

### 4.4. So Sánh Đầy Đủ Các Phương Pháp

| Phương pháp | Mô tả | Avg Accuracy |
|-------------|-------|-------------|
| Base model (no training) | Dùng model gốc, không có CoT | 60.1% |
| Base + CoT prompting | Dùng model gốc, thêm "think step by step" | 62.9% |
| SFT, no CoT | Fine-tune chỉ trên (code, outcome), không có reasoning | 66.7% |
| SFT + A Priori CoT | Fine-tune với reasoning do LLM tự sinh | **49.3% ← THẤT BẠI** |
| SFT + Hindsight (GPT-OSS-20B) | Fine-tune với Hindsight CoT, teacher = GPT-OSS-20B | 69.6% |
| SFT + Hindsight (QwQ-32B) | Fine-tune với Hindsight CoT, teacher = QwQ-32B | **73.0%** |

**Kết luận**:
- A Priori CoT tệ hơn cả không training (49.3% < 60.1%) → nguy hiểm!
- Hindsight CoT cải thiện 6-13% so với baseline tốt nhất (SFT no CoT)
- Teacher model tốt hơn (QwQ-32B > GPT-OSS-20B) cho student tốt hơn

---

## 5. Pipeline Tạo 27.000 Mẫu Training

Quy trình 4 bước để tạo dataset lớn và đa dạng:

### Bước 1: Tạo 1.600 Bài Toán Đa Dạng

```
GPT-4o được yêu cầu:
→ Liệt kê 10 domain liên quan đến parallel programming
   (ví dụ: numerical computation, string processing, sorting, graph algorithms...)
→ Mỗi domain: tạo 8 bài toán seed (mô tả input/output rõ ràng)
→ Mỗi bài seed: tạo 20 biến thể (thay đổi kích thước, kiểu dữ liệu, constraints)

10 × 8 × 20 = 1.600 bài toán tổng cộng
```

**Ví dụ bài toán seed** (domain: numerical):
> "Cho vector A và B kích thước n, tính dot product. Input: 2 mảng float. Output: 1 scalar float."

**Ví dụ biến thể**:
- "Tính dot product của 2 mảng integer"
- "Tính dot product của n cặp vector (batch)"
- "Tính weighted dot product với weight vector thứ 3"
- ...

**Quan trọng**: GPT-4o cũng tạo **harness kiểm tra** cho mỗi bài toán:
```cpp
bool validate(function<double(vector<double>&, vector<double>&)> parallel_impl) {
    // Sinh test cases ngẫu nhiên
    vector<double> a = random_vector(1000);
    vector<double> b = random_vector(1000);
    
    // So sánh với reference serial implementation
    double serial_result = serial_dot_product(a, b);
    double parallel_result = parallel_impl(a, b);
    
    return abs(serial_result - parallel_result) < 1e-6;
}
```

### Bước 2: Tạo Code Candidates Đa Dạng

Mục tiêu: tạo nhiều implementation khác nhau cho mỗi bài toán để có đa dạng về **phong cách**, **chiến lược parallelism**, và **correctness**.

```
Mô hình được dùng để generate code:
- Llama-3.3-70B
- Llama-3.1-8B
- Gemma-3-27B
- Phi-4

Mỗi model tạo 4 implementation với prompt khác nhau:
- "Implement với OpenMP parallel for"
- "Implement với OpenMP task"
- "Implement tối ưu cho cache locality"
- "Implement tối ưu cho ít thread contention nhất"
```

**Với ThreadSanitizer dataset**: Cố ý tạo **cả code có race lẫn code không có race**:
- 50% code sạch (dùng reduction, atomic, lock đúng cách)
- 50% code có race (không dùng synchronization cho shared variable)

**Với Caliper dataset**: Tạo code với **mức overhead khác nhau**:
- Code với ít barrier (overlap tính toán và communication)
- Code với nhiều false sharing
- Code với load imbalance
- Code với tối ưu memory access

Tất cả code đều dùng **OpenMP** làm framework parallelism (C/C++).

### Bước 3: Chạy Tool Thật Để Lấy "Ground Truth"

```
y_tsan ← ThreadSanitizer(code, harness)
```

Quy trình chi tiết cho ThreadSanitizer:
1. Compile code với `g++ -fsanitize=thread -g`
2. Chạy binary với harness
3. Parse output để extract race reports
4. Output: list of `{type: "read/write race", locations: [...]}`

```
y_caliper ← Caliper(code, harness)
```

Quy trình chi tiết cho Caliper (phức tạp hơn):
1. **GPT-4o xác định OpenMP parallel regions** (start line, end line)
2. **Instrument code** — chèn markers theo thứ tự từ dưới lên (để không shift line numbers):
   ```cpp
   // Trước instrument:
   #pragma omp parallel for
   for (int i = 0; i < n; i++) {
       result += a[i];
   }
   
   // Sau instrument:
   #include <caliper/cali.h>
   ...
   CALI_MARK_BEGIN("parallel_region_1");
   #pragma omp parallel for
   for (int i = 0; i < n; i++) {
       result += a[i];
   }
   CALI_MARK_END("parallel_region_1");
   ```
3. Profile với 4 mức thread: 4, 16, 64, 128
4. Output: `{work_percentage: {4: 96, 16: 76, 64: 44, 128: 47}}`

### Bước 4: Tạo Hindsight CoT Bằng Teacher Model

```
Teacher: QwQ-32B hoặc GPT-OSS-20B

Input prompt:
"Đây là đoạn code C++ với OpenMP:
[x_code]

ThreadSanitizer phát hiện: [y_tsan]

Hãy phân tích code từng bước, giải thích tại sao có/không có 
data race. Suy luận đi từ code → kết luận, KHÔNG nhắc đến 
'tôi đã biết kết quả là X'."

Output: chuỗi suy luận z (dài 2000-5000 token)
```

**Hyperparameters của Teacher** (QwQ-32B):
- Temperature: 0.999 (high — tạo đa dạng reasoning styles)
- Top-p: 0.95
- Max tokens: 32.768

**Kết quả**: Mỗi tool có **27.000 training samples** `(x_code, z, y)`.

---

## 6. Training Chi Tiết

### 6.1. Setup Training

```python
# Pseudo-code setup
from trl import SFTTrainer
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")

# Format training sample:
# <|im_start|>user
# [source code]
# <|im_end|>
# <|im_start|>assistant  
# [reasoning trace z]
# [outcome y]
# <|im_end|>

# Loss: completion-only SFT
# Chỉ tính loss trên phần assistant response
# KHÔNG tính loss trên phần user (source code)
# → Model học sinh ra z và y, không phải học thuộc code input
```

### 6.2. Hyperparameters

| Thông số | Giá trị | Lý do |
|---------|---------|-------|
| Sequence length | 16.384 token | Code dài + reasoning trace dài |
| Precision | bfloat16 | Tốt cho training stability, tiết kiệm memory |
| FSDP | Full-shard | Chia model qua nhiều GPU (model lớn) |
| Epochs | 1 | Đủ với 27K samples, tránh overfitting |
| Learning rate | 1×10⁻⁵ | Conservative — fine-tuning (không phải train from scratch) |
| LR scheduler | Cosine | Giảm dần theo cosine curve |
| Warmup | 5% steps đầu | Tránh learning rate shock lúc đầu |
| AdamW β₁/β₂ | 0.9 / 0.95 | Standard for LLM fine-tuning |
| Weight decay | 1×10⁻⁴ | Regularization nhẹ |

### 6.3. Models Được Train

| Model | Parameters | Kiến trúc |
|-------|-----------|----------|
| Qwen-2.5-7B-Instruct | 7B | Transformer, GQA |
| Qwen-2.5-14B-Instruct | 14B | Transformer, GQA |
| Qwen-2.5-32B-Instruct | 32B | Transformer, GQA |
| Llama-3.1-8B-Instruct | 8B | Transformer, GQA |

**Lưu ý**: Đây là **full fine-tuning** (không phải QLoRA) vì nhóm tác giả có GPU cluster của Lawrence Livermore National Laboratory. ThreadLearn dùng QLoRA vì resource hạn chế hơn.

---

## 7. Kết Quả Chi Tiết

### 7.1. ThreadSanitizer World Model

**Evaluation dataset**: DataRaceBench — ~200 OpenMP programs với label race/no-race do chuyên gia annotate.

**Bảng kết quả đầy đủ** (accuracy %):

| Model | Base no CoT | Base + CoT prompt | SFT no CoT | SFT + GPT-OSS-20B | SFT + QwQ-32B |
|-------|------------|-------------------|-----------|-------------------|--------------|
| Qwen-2.5-32B | 67.0 | 66.4 | 70.5 | 72.4 | **75.2** |
| Qwen-2.5-14B | 62.2 | 67.1 | 67.8 | 69.7 | **74.2** |
| Qwen-2.5-7B | 58.5 | 64.3 | 64.4 | 66.5 | **72.8** |
| Llama-3.1-8B | 52.6 | 53.9 | 64.2 | 69.6 | **69.7** |
| **Avg** | **60.1** | **62.9** | **66.7** | **69.6** | **73.0** |

**Phân tích từng cột**:

**Column 1 (Base no CoT)**: Model gốc chưa fine-tune, không có reasoning
- Qwen-2.5-32B baseline 67% → model lớn đã học được ít về parallel code từ pretraining
- Llama-3.1-8B chỉ 52.6% → gần random (50%)

**Column 2 (Base + CoT prompting)**: Thêm "think step by step" trong prompt
- Cải thiện nhỏ (+2.8% avg) — reasoning có giúp nhưng model chưa được train để reason về parallel code
- Llama-3.1-8B hầu như không cải thiện (52.6% → 53.9%)

**Column 3 (SFT no CoT)**: Fine-tune chỉ trên (code, outcome), không có reasoning trace
- Cải thiện +3.8% avg so với base
- Llama 8B tăng mạnh nhất (52.6% → 64.2%) — small model benefit nhiều nhất từ fine-tuning

**Column 4 (A Priori CoT — KHÔNG HIỂN THỊ trong bảng vì quá tệ)**:
- Paper báo cáo tất cả collapse về 49.3% — tệ hơn random!
- Đây là lý do cột này bị bỏ khỏi bảng chính, chỉ mention trong ablation

**Column 5 (SFT + Hindsight QwQ-32B)**: Best performance
- +6.3% avg so với SFT no CoT → Hindsight CoT cộng thêm đáng kể
- Qwen-2.5-7B đạt 72.8% — model 7B với Hindsight CoT gần bằng Qwen-32B không fine-tune (67%)!

**Quan sát thú vị — Teacher-Student compatibility**:
```
Llama-3.1-8B + GPT-OSS-20B teacher: 69.6%
Qwen-2.5-7B + GPT-OSS-20B teacher:  66.5%

→ Llama 8B học tốt hơn từ GPT-OSS-20B dù Qwen 7B có base accuracy cao hơn
→ Teacher-student architecture compatibility quan trọng
→ Không phải cứ teacher to hơn là tốt hơn cho mọi student
```

**Ảnh hưởng kích thước dataset** (với Qwen-2.5-7B + QwQ-32B CoT):
```
6K samples:  66.2%
13K samples: 70.4%
27K samples: 72.8%

→ Scaling đều — nhiều data hơn → tốt hơn (với small model)
→ Qwen-2.5-32B ít nhạy cảm hơn với data size (already strong)
```

**Model lớn → reasoning trace ngắn hơn**:
```
Qwen-2.5-32B: 3.050 token avg per response → 2.184 TFLOPs
Qwen-2.5-14B: 3.915 token avg per response → 3.094 TFLOPs
Qwen-2.5-7B:  5.216 token avg per response → 2.347 TFLOPs
Llama-3.1-8B: 5.283 token avg per response → 3.066 TFLOPs

→ 32B model đạt accuracy cao nhất với ÍT FLOPs nhất
→ Nó suy luận ngắn gọn, chính xác, không lan man
→ Khi chọn model: xét cả accuracy LẪN inference cost
```

### 7.2. Caliper World Model

**Task**: Pairwise comparison — cho 2 đoạn code, predict cái nào có work% cao hơn.

**Evaluation dataset**: ParEval — 54 OpenMP problems từ HPC benchmark suite.

| Model | Avg Base | Avg After SFT | Delta |
|-------|---------|---------------|-------|
| Qwen-2.5-32B | 43.0% | 59.7% | +16.7% |
| Qwen-2.5-7B | 46.9% | 55.8% | +8.9% |
| Llama-3.1-8B | 49.3% | 58.6% | +9.3% |
| **Avg** | **46.4%** | **58.0%** | **+11.6%** |

**Lưu ý quan trọng**: Base model thậm chí **kém cả random (50%)** trên task này → đây là task cực khó, model gốc chưa bao giờ thấy data như này.

**Pattern thú vị**: Accuracy phụ thuộc vào **margin** giữa 2 code:
```
Margin 0-10%:  accuracy ~55% (gần random — khó phân biệt)
Margin 10-30%: accuracy ~65%
Margin >30%:   accuracy ~75% (dễ phân biệt)

→ Model học được trực giác tốt về magnitude, nhưng khó với marginal cases
```

---

## 8. Ứng Dụng: Race-Fixing Agent

Sau khi train PCWM, nhóm tác giả dùng nó trong **vòng lặp tự động sửa race**:

### 8.1. Kiến Trúc Agent

```
┌─────────────────────────────────────────────────────────┐
│                    Race-Fixing Loop                      │
│                                                          │
│  x_code (input)                                         │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────┐                                            │
│  │  PCWM   │ → z (reasoning), y (race report)           │
│  └────┬────┘                                            │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────────┐                                        │
│  │ Actor LLM   │ nhận: x_code + z + y                   │
│  │ (Llama-70B) │ → e (edit instructions)                │
│  └────┬────────┘                                        │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────────┐                                        │
│  │ Apply Edit  │ x'_code = apply(x_code, e)             │
│  └────┬────────┘                                        │
│       │                                                  │
│       ▼                                                  │
│  Race fixed? → Yes → Done                               │
│              → No  → Lặp lại (tối đa N vòng)            │
└─────────────────────────────────────────────────────────┘
```

### 8.2. Kết Quả Race-Fixing (sau 1 vòng)

| Actor Model | Oracle feedback | Self-reflection | PCWM 7B | PCWM 14B |
|------------|----------------|----------------|---------|---------|
| Llama-3.1-70B | 79.4% | 73.8% | 75.8% | **78.3%** |
| Gemma-3-27B | 69.3% | 63.9% | 69.7% | **71.0%** |
| **Avg** | **74.4%** | **68.9%** | **72.8%** | **74.7%** |

Metric: % programs không còn race condition sau 1 vòng sửa.

### 8.3. Phát Hiện Quan Trọng: PCWM 14B Vượt Oracle!

```
Oracle feedback:  74.4%  (kết quả thật từ ThreadSanitizer)
PCWM 14B:         74.7%  ← CAO HƠN oracle!
```

**Tại sao?**

Oracle chỉ cho biết: "có race tại dòng X" — thông tin thô.

PCWM cung cấp: "có race tại dòng X, **VÌ** hai thread đồng thời đọc-ghi biến Y mà không có synchronization, cụ thể là pattern Z" — thông tin **phong phú về ngữ nghĩa**.

Actor LLM nhận thông tin phong phú hơn → hiểu rõ vấn đề hơn → sửa chính xác hơn → **fix rate cao hơn**.

Đây là insight quan trọng nhất của paper: **Causal reasoning về bug quan trọng hơn chỉ biết bug ở đâu**.

### 8.4. So Sánh Với Commercial Models

```
commercial model + oracle:      ít cải thiện (gpt-4.1-mini, claude-haiku-3)
commercial model + PCWM:        tương tự

→ Commercial models đã đủ mạnh để tự suy luận về race
→ PCWM benefits nhất cho open-source models (Llama, Gemma)
```

---

## 9. Phân Tích Chi Phí Tính Toán

### 9.1. Training Cost

```
Với full fine-tuning (không QLoRA):
- Qwen-2.5-7B:  cần ~4 × A100 80GB, ~48 giờ
- Qwen-2.5-32B: cần ~8 × A100 80GB, ~96 giờ

Với QLoRA r=16 (như ThreadLearn):
- Qwen2.5-Coder-1.5B: cần 1 × T4 16GB, ~6-8 giờ trên Colab
```

### 9.2. Inference Cost So Sánh

| Model | FLOPs/response | Token/response | Accuracy |
|-------|---------------|---------------|---------|
| Qwen-2.5-32B | 2.184 TFLOPs | 3.050 | **75.2%** |
| Qwen-2.5-14B | 3.094 TFLOPs | 3.915 | 74.2% |
| Qwen-2.5-7B | 2.347 TFLOPs | 5.216 | 72.8% |
| Llama-3.1-8B | 3.066 TFLOPs | 5.283 | 69.7% |

**Insight**: 32B model tốt nhất cả accuracy LẪN FLOPs. Đây là "sweet spot" — reasoning ngắn gọn và chính xác.

7B model dùng hơn gấp đôi tokens so với 32B để đạt accuracy thấp hơn → suy luận lòng vòng, không tập trung.

---

## 10. Tại Sao Hindsight CoT Hiệu Quả? (Phân Tích Sâu)

### 10.1. Góc Nhìn Học Thuật

**A Priori CoT** tạo ra bài toán: "Từ code → đoán kết quả → sinh reasoning phù hợp với đoán đó"

Đây là bài toán **khó** vì:
- Thread interaction space-state không thể enumerate bằng đọc code
- Model phải đồng thời: (1) đoán đúng kết quả, (2) sinh reasoning đúng, (3) 2 cái khớp nhau
- Xác suất thất bại cao → nhiều training sample sai → cascade failure

**Hindsight CoT** tạo ra bài toán: "Biết kết quả → tìm reasoning dẫn đến kết quả đó"

Đây là bài toán **dễ hơn nhiều** vì:
- Chỉ cần tìm 1 trong N con đường reasoning dẫn đến kết quả đúng
- Không cần đồng thời đoán kết quả và sinh reasoning
- Mọi training sample đều có kết quả ĐÚNG (từ tool thật) → không có negative signal từ wrong predictions

### 10.2. Tương Tự Trong Học Người

| A Priori CoT | Hindsight CoT |
|-------------|--------------|
| Học toán bằng tự mò | Xem đáp án rồi hiểu cách làm |
| Tự viết proof rồi check | Đọc proof có sẵn, hiểu từng bước |
| Thi xong không biết đúng sai | Chấm bài ngay sau mỗi bước |

Hindsight learning là cách học hiệu quả hơn khi bài toán quá khó để tự giải từ đầu.

### 10.3. Giới Hạn

Hindsight CoT không phải silver bullet:
- Vẫn cần tool thật để lấy ground truth → vẫn cần infrastructure
- Teacher model viết reasoning sai (dù biết đáp án) → cần review
- Model học reasoning trace của teacher, không phải của tool developer → có thể học reasoning style của teacher

---

## 11. Sự Khác Biệt Giữa PCWMs Và ThreadLearn

| Aspect | PCWMs | ThreadLearn |
|--------|-------|------------|
| Language | C/C++ với OpenMP | JavaScript + Python |
| Parallelism model | Shared memory (OpenMP) | Event loop + threading |
| Detection tool | ThreadSanitizer (runtime) | race_detector.py (static) |
| Base model | Qwen2.5-7/14/32B, Llama-8B | Qwen2.5-Coder-1.5B |
| Fine-tuning method | Full fine-tune | QLoRA r=16 |
| CoT technique | Hindsight CoT (same!) | Hindsight CoT |
| End goal | Mô phỏng tool | Detect + Fix |
| Evaluation | DataRaceBench, ParEval | Custom JS/Python benchmark |

**ThreadLearn đóng góp gì mới so với PCWMs**:
1. Áp dụng Hindsight CoT cho JavaScript (NodeCB bug patterns) — PCWMs chỉ dùng OpenMP/C++
2. Static analysis làm grounding (không cần chạy code) — phù hợp partial code
3. Kết hợp RAG + fine-tuned LLM — PCWMs không có RAG
4. Model nhỏ (1.5B) cho deployment local — PCWMs dùng model 7B+
5. End-to-end detect + fix pipeline — PCWMs chỉ detect (world model)

---

## 12. Công Việc Tương Lai (Theo Paper)

1. **Mở rộng ngoài OpenMP**: MPI (distributed memory), CUDA (GPU), pthreads (POSIX)
2. **Mở rộng tool**: Helgrind, Valgrind, Address Sanitizer, custom profilers
3. **Khó hơn về exploration**: Tạo code phức tạp hơn, nhiều interaction pattern hơn
4. **Cross-language**: Transfer từ OpenMP → MPI patterns

---

## 13. Tóm Tắt Nhanh

```
PCWMs (arXiv 2026)
├── Vấn đề: LLM kém với parallel code (thiếu data, khó suy luận)
├── Giải pháp: Train LLM mô phỏng tool (World Model)
│
├── 2 tool được mô phỏng:
│   ├── ThreadSanitizer: detect data race trong OpenMP C++ code
│   └── Caliper: đo work percentage (performance profiling)
│
├── Kỹ thuật cốt lõi: Hindsight Chain-of-Thought
│   ├── Vấn đề A Priori CoT: tất cả model collapse về 49.3% (THẤT BẠI)
│   ├── Hindsight: biết kết quả thật TRƯỚC, rồi viết reasoning dẫn đến kết quả
│   ├── Constraint: reasoning phải forward (code → kết luận), không backward
│   └── Teacher model: QwQ-32B hoặc GPT-OSS-20B
│
├── Dataset: 27K samples per tool
│   ├── 1.600 bài toán (10 domain × 8 seed × 20 biến thể)
│   ├── 4 open-weight models sinh code candidate
│   └── Ground truth từ tool thật (TSan + Caliper)
│
├── Kết quả ThreadSanitizer:
│   ├── Qwen-2.5-7B:  64.3% → 72.8% (+8.5%)
│   ├── Qwen-2.5-32B: 66.4% → 75.2% (+8.8%)
│   └── A Priori CoT: 49.3% (THẤT BẠI HOÀN TOÀN)
│
├── Kết quả Caliper:
│   └── Avg: 46.4% → 58.0% (+11.6%)
│
├── Race-fixing agent:
│   └── PCWM 14B (74.7%) > Oracle feedback (74.4%)!
│       (Causal reasoning > just knowing bug location)
│
└── Insight chính:
    ├── Hindsight CoT giải quyết training distribution mismatch
    ├── Reasoning trace giúp actor LLM fix tốt hơn oracle
    └── Model to không phải luôn tốt hơn (32B < FLOPs nhưng > accuracy)
```

---

## 14. Ý Nghĩa Với ThreadLearn

### 14.1. Validation Hướng Đi

PCWMs chứng minh 3 điều ThreadLearn dựa vào:
1. **LLM có thể học reasoning về concurrency** nếu có đủ dữ liệu training tốt
2. **Hindsight CoT là cần thiết** — a priori CoT sẽ thất bại (49.3% collapse)
3. **Small model fine-tuned có thể tốt hơn large model không fine-tuned** — Qwen 7B fine-tuned ≈ Qwen 32B no fine-tune

### 14.2. Hướng Dẫn Cụ Thể Cho ThreadLearn Implementation

**Cho AI1-03 (fine-tuning)**:
```python
# ĐÚNG — Hindsight CoT approach
def create_training_sample(code, race_detector_output):
    # race_detector_output là "ground truth" từ static analysis
    # Yêu cầu teacher model viết reasoning DẪN ĐẾN kết quả đó
    prompt = f"""Code sau có kết quả phân tích: {race_detector_output}
    
Hãy phân tích từng bước code này, giải thích lý do tại sao 
kết quả là như vậy. Bắt đầu từ code, đừng nhắc đến kết quả đã biết."""
    
    reasoning = teacher_model.generate(code + prompt)
    return (code, reasoning, race_detector_output)

# SAI — A Priori CoT (SẼ COLLAPSE)
def create_training_sample_wrong(code):
    prompt = "Code này có race condition không? Suy luận từng bước."
    reasoning_and_prediction = model.generate(code + prompt)
    # Nếu model đoán sai → training sample sai → collapse!
```

**Cho dataset creation**:
- Cần đa dạng code samples (nhiều pattern, nhiều language style)
- Ground truth từ `race_detector.py` (static analysis) hoặc chạy test thật
- Teacher model viết reasoning (có thể dùng Claude-3.5-Sonnet hoặc GPT-4o)

**Cho model selection**:
- 1.5B với QLoRA sẽ đạt accuracy thấp hơn 7B full fine-tune
- Nhưng vẫn có improvement đáng kể so với baseline (theo scaling law trong paper)
- Có thể cần nhiều data hơn để compensate model nhỏ hơn

### 14.3. Điểm Khác Biệt ThreadLearn vs PCWMs (Đóng Góp Mới)

| ThreadLearn Contribution | Tại Sao Quan Trọng |
|------------------------|-------------------|
| JavaScript event loop bugs (NodeCB patterns) | PCWMs chỉ cover OpenMP/C++ — JS hoàn toàn khác |
| Static analysis làm grounding (không cần compile) | PCWMs cần runtime → không dùng được cho partial code |
| RAG-augmented generation | PCWMs không có RAG — thiếu context từ similar fixed bugs |
| 1.5B deployable model | PCWMs model nhỏ nhất là 7B — không thể local deploy |
| Combined detect + fix pipeline | PCWMs chỉ làm world model (detect), ThreadLearn làm cả hai |
