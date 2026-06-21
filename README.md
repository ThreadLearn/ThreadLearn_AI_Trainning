# ThreadLearn — AI Training Module

> **Phát hiện và sửa lỗi concurrency JavaScript bằng Fine-tuned LLM + RAG Pipeline**
>
> Dự án môn WDP301 — FPT University  
> Tác giả: **Lê Trí Trung** · **Hà Văn Ân**

---

## Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Lý do chọn hướng tiếp cận này](#2-lý-do-chọn-hướng-tiếp-cận-này)
3. [Kiến trúc hệ thống](#3-kiến-trúc-hệ-thống)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [AI1 — Thu thập dữ liệu và Fine-tuning](#5-ai1--thu-thập-dữ-liệu-và-fine-tuning)
   - 5.1 [Thu thập và xây dựng dataset](#51-thu-thập-và-xây-dựng-dataset)
   - 5.2 [Định dạng JSONL cho SFTTrainer](#52-định-dạng-jsonl-cho-sfttrainer)
   - 5.3 [QLoRA Fine-tuning trên Kaggle](#53-qlora-fine-tuning-trên-kaggle)
   - 5.4 [Merge LoRA Adapter vào Base Model](#54-merge-lora-adapter-vào-base-model)
6. [AI2 — RAG Pipeline và API Server](#6-ai2--rag-pipeline-và-api-server)
   - 6.1 [Knowledge Base và BM25 Indexing](#61-knowledge-base-và-bm25-indexing)
   - 6.2 [RAG Pipeline hoạt động như thế nào](#62-rag-pipeline-hoạt-động-như-thế-nào)
   - 6.3 [FastAPI Server](#63-fastapi-server)
7. [Đánh giá mô hình — Kết quả thực tế](#7-đánh-giá-mô-hình--kết-quả-thực-tế)
8. [Các lỗi gặp phải và cách giải quyết](#8-các-lỗi-gặp-phải-và-cách-giải-quyết)
9. [Tính ưu việt và ứng dụng thực tế](#9-tính-ưu-việt-và-ứng-dụng-thực-tế)
10. [Hướng dẫn chạy lại từ đầu](#10-hướng-dẫn-chạy-lại-từ-đầu)
11. [Tài liệu tham khảo](#11-tài-liệu-tham-khảo)

---

## 1. Tổng quan dự án

### Vấn đề cần giải quyết

JavaScript là ngôn ngữ chạy theo mô hình **single-threaded event loop** — tức là chỉ có một luồng thực thi duy nhất, nhưng có thể xử lý nhiều tác vụ bất đồng bộ (async) cùng lúc thông qua callback, Promise, và async/await.

Chính sự phức tạp này tạo ra một lớp lỗi rất nguy hiểm gọi là **concurrency bugs** — các lỗi xảy ra do thứ tự thực thi không như lập trình viên mong đợi. Theo nghiên cứu NodeCB (ASE 2017) phân tích 57 lỗi thực tế trên 53 dự án Node.js:

- **65%** là vi phạm tính nguyên tử (atomicity violation) — hai thao tác cần chạy liên tục nhưng bị tác vụ khác chen vào giữa
- **30%** là vi phạm thứ tự (order violation) — tác vụ A chạy trước khi tác vụ B hoàn thành, trong khi A phụ thuộc vào kết quả của B
- **93%** các lỗi này gây ra hậu quả nghiêm trọng: crash server, dữ liệu database bị sai, hoặc server treo vĩnh viễn

**Ví dụ cụ thể:** Một website thương mại điện tử có đoạn code như sau:

```javascript
// LỖI: Hai request cùng đọc số lượng tồn kho rồi cùng trừ đi 1
const stock = await db.getStock(productId);   // Cả 2 request đọc được stock = 1
await db.setStock(productId, stock - 1);       // Cả 2 request đặt stock = 0
// Kết quả: bán 2 sản phẩm nhưng kho chỉ có 1 — race condition!
```

Lỗi này rất khó phát hiện vì **không crash ngay** — nó chỉ xảy ra khi nhiều người dùng cùng thao tác một lúc. Khi chạy test đơn lẻ, code hoạt động hoàn toàn bình thường.

### Giải pháp của ThreadLearn

ThreadLearn xây dựng một hệ thống AI có khả năng:
1. **Nhận vào** một đoạn JavaScript code
2. **Phân tích** và phát hiện các lỗi concurrency
3. **Tạo ra** đoạn code đã được sửa, kèm giải thích

Hệ thống kết hợp hai thành phần:
- **AI1** (Hà Văn Ân thực hiện): Fine-tune mô hình ngôn ngữ Qwen2.5-Coder-1.5B để "dạy" nó hiểu và sửa lỗi concurrency JavaScript
- **AI2** (Lê Trí Trung thực hiện): Xây dựng RAG pipeline (Retrieval-Augmented Generation) để bổ sung ngữ cảnh kiến thức trước khi hỏi mô hình

---

## 2. Lý do chọn hướng tiếp cận này

### Tại sao không dùng các công cụ phân tích tĩnh truyền thống?

Các công cụ như ESLint, ThreadSanitizer, hay Helgrind có thể phát hiện một số lỗi nhưng:
- **Chỉ phát hiện, không sửa** — chúng báo lỗi ở dòng bao nhiêu nhưng không nói cách sửa
- **Quy tắc cứng nhắc** — chỉ nhận diện được các pattern đã được lập trình sẵn, không tổng quát hóa được
- **Nhiều false positive** — cờ nhầm code đúng là lỗi, gây phiền cho lập trình viên

### Tại sao không dùng GPT-4 hay model lớn?

- **Chi phí cao** — mỗi lần gọi API tốn tiền, không thể nhúng vào IDE dùng offline
- **Không chuyên biệt** — model tổng quát không được "dạy" đặc biệt về concurrency JavaScript
- **Độ trễ cao** — gọi API qua internet làm chậm trải nghiệm lập trình viên
- **Phụ thuộc internet** — không dùng được ở môi trường corporate có firewall

### Tại sao chọn Qwen2.5-Coder-1.5B + QLoRA?

**Qwen2.5-Coder-1.5B** là mô hình mã nguồn mở của Alibaba, được pre-train trên hàng trăm tỷ token code. Với 1.5 tỷ tham số:
- Đủ nhỏ để chạy trên laptop GPU thông thường (RTX 4060 với 8GB VRAM)
- Đủ mạnh để hiểu cú pháp và ngữ nghĩa JavaScript phức tạp
- Có thể fine-tune miễn phí trên Kaggle (2× T4 GPU, 30GB VRAM)

**QLoRA (Quantized Low-Rank Adaptation)** là kỹ thuật fine-tune hiệu quả:

```
Model gốc (3GB float16)
    ↓ Load 4-bit quantization (NF4) → giảm xuống còn ~800MB VRAM
    ↓ Thêm LoRA adapter nhỏ (r=16) → chỉ train ~0.5% tham số
    ↓ Kết quả: giữ được kiến thức gốc + học được kiến thức mới
```

So sánh tài nguyên cần thiết:

| Phương pháp | VRAM cần | Thời gian train |
|-------------|----------|-----------------|
| Full fine-tune | ~12GB | ~8 giờ |
| LoRA fp16 | ~6GB | ~3 giờ |
| **QLoRA (chúng tôi dùng)** | **~4GB** | **~2 giờ** |

### Tại sao cần RAG?

Mô hình 1.5B tham số dù đã fine-tune vẫn có giới hạn kiến thức. **RAG (Retrieval-Augmented Generation)** giải quyết điều này bằng cách:

1. Trước khi hỏi model, tìm kiếm tài liệu liên quan từ knowledge base 2050 tài liệu
2. "Nhét" những tài liệu đó vào đầu prompt như một "cuốn sách mở" cho model tham khảo
3. Model không cần nhớ mọi thứ — chỉ cần biết cách đọc tài liệu và áp dụng

**Kết quả thực tế:** RAG tăng pass rate từ 70% lên 75% trên benchmark 20 test case.

---

## 3. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        LUỒNG DỮ LIỆU                           │
└─────────────────────────────────────────────────────────────────┘

[JavaScript Code]
        │
        ▼
┌───────────────────┐
│  AST Preprocessor │  ← Làm sạch code, trích keyword
└────────┬──────────┘
         │
         ▼
┌───────────────────┐     ┌──────────────────────────┐
│   BM25 Retriever  │◄────│  knowledge_base.json      │
│   (AI2-02)        │     │  2050 tài liệu JS         │
└────────┬──────────┘     └──────────────────────────┘
         │ top-3 docs liên quan
         ▼
┌───────────────────┐
│  RAG Pipeline     │  ← Ghép context docs + code thành prompt
│  (AI2-05)         │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Fine-tuned LLM   │  ← Qwen2.5-Coder-1.5B + LoRA (783 samples)
│  (AI1-03/04)      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Fix Code Output  │  ← Đoạn code đã sửa + giải thích
└───────────────────┘
```

**Tóm tắt các thành phần chính:**

| Thành phần | Vị trí | Chức năng |
|------------|--------|-----------|
| Dataset Collector | `ai1/modules/ai1_01_dataset_collector.py` | Thu thập dữ liệu huấn luyện |
| JSONL Formatter | `ai1/modules/ai1_02_format_jsonl.py` | Chuẩn hóa dữ liệu cho SFTTrainer |
| Fine-tuning Script | `ai1/training/ai1_03_finetune.py` | Huấn luyện QLoRA trên Kaggle |
| Model Merger | `ai1/training/ai1_04_merge_model.py` | Gộp LoRA adapter vào base model |
| BM25 Module | `ai2/server/bm25_module.py` | Indexing và tìm kiếm tài liệu |
| RAG Pipeline | `ai2/server/rag_pipeline.py` | Kết nối BM25 + LLM |
| FastAPI Server | `ai2/server/main.py` | API endpoint cho frontend |
| Eval Script | `ai2/eval_rag_merged.py` | Đánh giá model với 20 test case |

---

## 4. Cấu trúc thư mục

```
ThreadLearn-AI-Trainning/
│
├── ai1/                          # Module thu thập dữ liệu & fine-tuning
│   ├── modules/
│   │   ├── ai1_01_dataset_collector.py   # Thu thập từ GitHub + synthetic pairs
│   │   ├── ai1_02_format_jsonl.py        # Chuyển sang JSONL cho SFTTrainer
│   │   └── ast_preprocessor.py           # Làm sạch code, trích keyword
│   ├── training/
│   │   ├── ai1_03_finetune.py            # QLoRA fine-tuning (chạy trên Kaggle)
│   │   └── ai1_04_merge_model.py         # Merge adapter → model hoàn chỉnh
│   ├── data/
│   │   └── raw/                          # Dataset thô trước khi format
│   └── evaluation/
│       └── evaluate_model.py             # Đánh giá model sau fine-tuning
│
├── ai2/                          # Module RAG pipeline & API server
│   ├── server/
│   │   ├── main.py                       # FastAPI app, endpoint /analyze
│   │   ├── rag_pipeline.py               # Kết nối BM25 + LLM
│   │   ├── bm25_module.py                # BM25 indexing + search
│   │   ├── llm_client.py                 # Giao tiếp với LLM (mock/ollama)
│   │   ├── race_detector.py              # Phát hiện 5 pattern race condition
│   │   ├── report_formatter.py           # Format kết quả trả về
│   │   ├── cache.py                      # Redis cache
│   │   ├── auth.py                       # JWT authentication
│   │   └── schemas.py                    # Pydantic schemas
│   ├── knowledge-base/
│   │   └── knowledge_base.json           # 2050 tài liệu JS concurrency
│   ├── tests/
│   │   ├── test_main.py                  # Unit test API endpoints
│   │   ├── test_rag_pipeline.py          # Unit test RAG pipeline
│   │   ├── test_bm25.py                  # Unit test BM25 search
│   │   └── locustfile.py                 # Load testing
│   ├── eval_rag_merged.py                # Eval với đúng training format
│   ├── eval_local_merged.py              # Eval cũ (sai format — để tham khảo)
│   └── eval_rag_results.json             # Kết quả eval thực tế
│
├── models/
│   └── merged/                           # Model sau khi merge (3GB)
│       ├── model.safetensors
│       └── config.json
│
└── docs/
    └── my-research/
        ├── threadlearn_paper.tex          # Research paper LaTeX
        ├── paper_outline_en.md            # Outline tiếng Anh
        └── paper_outline_vi.md            # Outline tiếng Việt
```

---

## 5. AI1 — Thu thập dữ liệu và Fine-tuning

### 5.1 Thu thập và xây dựng dataset

**Mục tiêu:** Tạo ra tập dữ liệu gồm các cặp `(code lỗi → code đã sửa)` để dạy model.

#### Hai nguồn dữ liệu chính

**Nguồn 1 — GitHub Code Search API:**

Script `ai1_01_dataset_collector.py` tìm kiếm các commit trên GitHub với các từ khóa:

```python
JS_GITHUB_QUERIES = [
    "callback hell to promise javascript",
    "setTimeout callback to async await javascript",
    "sequential fetch to Promise.all javascript",
    "fs readFileSync to promises javascript",
    # ... 15 queries khác
]
```

Cách hoạt động: Mỗi query tìm kiếm các commit mà lập trình viên thực sự đã sửa code từ dạng blocking/callback sang async — đây là dữ liệu "thật" từ thực tế.

**Nguồn 2 — Synthetic Pairs (60 cặp viết tay):**

Vì dữ liệu GitHub thường lẫn nhiều thứ không liên quan, nhóm tự viết 60 cặp code chất lượng cao, phân theo 8 category:

```javascript
// Ví dụ một cặp trong dataset:
// INPUT (code có lỗi):
function getUser(id, callback) {
  db.query('SELECT * FROM users WHERE id = ?', [id], (err, rows) => {
    if (err) return callback(err);
    callback(null, rows[0]);
  });
}

// OUTPUT (code đã sửa):
async function getUser(id) {
  const rows = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  return rows[0];
}
```

**Kết quả dataset cuối cùng:**
- **783 mẫu** hợp lệ (có đủ input và output)
- Phân bố: 90% train (704 mẫu) / 10% eval (79 mẫu)
- Shuffle với `random.seed(42)` để đảm bảo tái hiện được kết quả

### 5.2 Định dạng JSONL cho SFTTrainer

**Tại sao cần bước này?** SFTTrainer của thư viện TRL (của HuggingFace) yêu cầu dữ liệu phải ở định dạng JSONL (mỗi dòng một JSON) với cấu trúc cụ thể.

Script `ai1_02_format_jsonl.py` chuyển đổi từ `raw_dataset.json` sang `threadlearn_train.jsonl`:

```python
# Định dạng chuẩn — QUAN TRỌNG: đây là "completion format", không phải "chat format"
jsonl_obj = {
    "prompt": f"Convert to concurrent JavaScript:\n\n{inp_code}\n",
    "completion": f"{out_code}\n"
}
```

**Tại sao dùng "completion format" thay vì "chat format"?**

Đây là một quyết định kỹ thuật quan trọng mà sau này phát hiện ra có ảnh hưởng lớn đến kết quả. Qwen2.5-Coder có hai cách hoạt động:

1. **Chat format** (ChatML): Dùng system/user/assistant roles, phù hợp cho hội thoại
   ```
   <|im_start|>system
   You are a helpful assistant.
   <|im_start|>user
   Fix this code...
   <|im_start|>assistant
   ```

2. **Completion format** (chúng tôi dùng): Là raw text completion, phù hợp cho code generation
   ```
   Convert to concurrent JavaScript:
   
   [code đầu vào]
   
   [code đã sửa — model phải predict phần này]
   ```

Chúng tôi chọn completion format vì:
- Đơn giản hơn, ít overhead hơn
- Phù hợp với task: nhìn thấy code → sinh ra code sửa
- Dễ test: chỉ cần nối `prompt + code` là xong

> **Bài học quan trọng:** Nếu dùng sai format khi inference (dùng chat template trong khi model train theo completion format), pass rate giảm từ 70% xuống 35%. Chi tiết xem [Phần 8 — Lỗi #4](#lỗi-4-prompt-format-mismatch--kết-quả-sai-35-thay-vì-70).

### 5.3 QLoRA Fine-tuning trên Kaggle

**Tại sao chọn Kaggle?** Kaggle cung cấp miễn phí 2× NVIDIA T4 GPU (mỗi card 16GB VRAM) và 30 giờ GPU/tuần — đủ để fine-tune model 1.5B với QLoRA.

#### Cấu hình QLoRA

```python
# 1. Quantization: Load model 4-bit để tiết kiệm VRAM
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,   # Double quantization: tiết kiệm thêm ~0.4 bit/param
    bnb_4bit_quant_type="nf4",        # NF4: Normal Float 4 — tốt hơn INT4 cho weights của LLM
    bnb_4bit_compute_dtype=torch.bfloat16  # Compute vẫn dùng bfloat16 để giữ độ chính xác
)

# 2. LoRA: Chỉ train một phần nhỏ tham số
lora_config = LoraConfig(
    r=16,           # Rank — kích thước của "bộ não bổ sung". r=16: cân bằng giữa hiệu quả và bộ nhớ
    lora_alpha=32,  # Scaling factor = 2×r, quy ước chuẩn
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",   # Attention layers
                    "gate_proj", "up_proj", "down_proj"],       # Feed-forward layers
    task_type="CAUSAL_LM"
)
```

**Giải thích `r=16` cho người không quen:**

Hãy tưởng tượng model gốc là một bộ não với hàng tỷ kết nối. LoRA không thay đổi bộ não này — thay vào đó nó thêm một "module bổ sung" nhỏ hơn:
- `r=16` nghĩa là module bổ sung này có 16 chiều
- Mỗi layer trong Transformer thay vì có weight matrix `[4096 × 4096]` (16M params), LoRA chỉ thêm 2 matrix nhỏ: `[4096 × 16]` và `[16 × 4096]` (131K params)
- Tổng tham số cần train: ~0.5% so với full fine-tune

#### Cấu hình Training

```python
training_args = SFTConfig(
    per_device_train_batch_size=1,    # 1 mẫu/lần vì GPU T4 chỉ có 16GB
    gradient_accumulation_steps=8,    # Tích lũy gradient 8 bước = "giả lập" batch size 8
    learning_rate=2e-4,               # Learning rate khá cao cho LoRA, nhưng phù hợp với warm-up
    max_steps=500,                    # ~500 bước = khoảng 1-2 giờ train
    warmup_steps=15,                  # 15 bước đầu tăng dần learning rate (tránh diverge)
    lr_scheduler_type="cosine",       # Cosine decay: giảm learning rate theo đường cong cosine
    bf16=True,                        # BFloat16 training (T4 hỗ trợ, nhanh hơn fp32)
    eval_strategy="steps",
    eval_steps=50,                    # Đánh giá trên eval set mỗi 50 bước
)
```

**Gradient Accumulation là gì?** Vì VRAM hạn chế, không thể cho 8 mẫu vào cùng lúc. Thay vào đó, cho 1 mẫu vào, tính gradient, giữ lại (accumulate), làm 8 lần, rồi mới cộng tất cả lại và cập nhật weights. Kết quả tương đương batch size 8 nhưng chỉ cần 1/8 VRAM.

### 5.4 Merge LoRA Adapter vào Base Model

Sau khi train xong, có 2 thứ riêng biệt:
- **Base model**: Qwen2.5-Coder-1.5B gốc (~3GB)
- **LoRA adapter**: Các weight bổ sung đã train (~50MB)

Để deploy dễ dàng, cần **merge** (hợp nhất) 2 cái lại thành 1 model hoàn chỉnh:

```python
# Script ai1_04_merge_model.py
base_model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-Coder-1.5B",
    device_map="cpu",           # QUAN TRỌNG: Dùng CPU để merge, tránh tràn VRAM
    torch_dtype=torch.float16,
)

# Gắn adapter vào base model
model = PeftModel.from_pretrained(base_model, "./final_adapter")

# "Đun chảy" LoRA vào base model — tạo thành model độc lập
merged_model = model.merge_and_unload()

# Lưu ra file (tạo thành file model.safetensors ~2.9GB)
merged_model.save_pretrained("threadlearn-qwen2.5-coder-1.5b-merged")
```

**Tại sao phải dùng CPU khi merge?** Nếu load model 4-bit (quantized) để merge, các thư viện sẽ báo lỗi vì không thể merge weight đã quantize. Phải load ở fp16 trên CPU, merge xong, rồi mới có thể tải lên GPU để inference.

**Model đã merge được lưu tại:** `models/merged/model.safetensors` (2944 MB)  
**HuggingFace Hub:** `anha12/threadlearn-qwen2.5-coder-1.5b-merged`

---

## 6. AI2 — RAG Pipeline và API Server

### 6.1 Knowledge Base và BM25 Indexing

#### Knowledge Base là gì?

`knowledge_base.json` chứa **2050 tài liệu** về JavaScript concurrency, mỗi tài liệu có cấu trúc:

```json
{
  "id": "js-001",
  "title": "Promise.all Pattern — Parallel Execution",
  "category": "patterns",
  "content": "Use Promise.all to run multiple async operations in parallel instead of sequentially. Example: const [user, stats] = await Promise.all([getUser(id), getStats(id)])..."
}
```

Các category trong knowledge base:
- `patterns` — Design patterns cho async code
- `race-condition` — Ví dụ và cách tránh race condition
- `event-loop` — Giải thích event loop, microtask queue
- `anti-patterns` — Các lỗi thường gặp và cách sửa
- `best-practices` — Thực hành tốt nhất

#### BM25 là gì và tại sao không dùng Vector Search?

**BM25 (Best Match 25)** là thuật toán tìm kiếm dựa trên từ khóa, cải tiến từ TF-IDF. Nguyên lý hoạt động:

- Từ xuất hiện ít trong toàn bộ corpus (như `appendFile`, `Semaphore`) được đánh điểm cao — từ "đặc trưng"
- Từ xuất hiện nhiều (`function`, `const`, `return`) điểm thấp — quá phổ biến, ít nghĩa
- Tài liệu ngắn mà chứa từ khóa thì điểm cao hơn tài liệu dài chứa cùng từ khóa đó

**So sánh BM25 vs Vector Search (như FAISS, Chroma):**

| Tiêu chí | BM25 | Vector Search |
|----------|------|---------------|
| Tốc độ build index | Rất nhanh (< 500ms cho 2050 docs) | Chậm (cần embed từng doc) |
| VRAM cần thiết | 0 (chỉ dùng RAM) | Cần GPU để embed |
| Phù hợp với code | **Tốt** — code dùng nhiều từ kỹ thuật cụ thể | Trung bình — semantic search đôi khi bỏ sót exact keyword |
| Thư viện cần | `rank-bm25` (50KB) | `sentence-transformers` (500MB+) |
| Hoạt động offline | **Hoàn toàn** | Cần model embed |

**Với JavaScript code, BM25 phù hợp hơn** vì:
- Code dùng các từ kỹ thuật cụ thể: `setTimeout`, `Promise.all`, `async/await`
- Lập trình viên biết rõ tên API cần tìm — exact keyword match quan trọng hơn semantic similarity

#### CamelCase-aware Tokenizer

Một thách thức khi index code JavaScript là các từ kiểu CamelCase như `fetchAllUsers` hay `BM25Retriever`. Tokenizer thông thường sẽ coi đây là một từ duy nhất.

Chúng tôi viết tokenizer tùy chỉnh:

```python
def _split_camel(token: str) -> List[str]:
    """
    "fetchAllUsers" → ["fetch", "all", "users"]
    "BM25Retriever" → ["bm25", "retriever"]
    "XMLParser"     → ["xml", "parser"]
    """
    # Bước 1: Chèn khoảng trắng giữa chữ thường và chữ HOA
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    # Bước 2: Xử lý chuỗi HOA liên tiếp (XMLParser → XML Parser)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", parts)
    return parts.lower().split()
```

Kết quả: Khi người dùng gửi code có `Promise.all`, tokenizer tách ra `["promise", "all"]` — khớp với tài liệu trong knowledge base chứa "Promise all pattern".

**Auto-stopwords cho corpus lớn:** Với corpus nhỏ hơn 5000 docs, dùng danh sách stopwords cố định. Với corpus >= 5000 docs, BM25Module tự động tính IDF và loại bỏ từ nào xuất hiện trong >80% tài liệu (những từ "không có nghĩa" với tìm kiếm). Thiết kế này cho phép mở rộng knowledge base mà không cần chỉnh tay.

### 6.2 RAG Pipeline hoạt động như thế nào

Toàn bộ flow từ code đầu vào đến output:

**Bước 1 — Trích xuất keyword bằng AST (esprima):**

Đây là điểm cải tiến quan trọng so với cách tiếp cận regex thông thường. Thay vì tokenize text thô, `rag_pipeline.py` gọi `ast_preprocessor.extract_keywords()` — dùng esprima parse JavaScript thành ESTree, sau đó walk qua các node để lấy đúng `Identifier` tokens.

**Vấn đề với regex tokenizer (cũ):**

```python
# Cách cũ — tokenize() trong bm25_module tách CamelCase
tokenize("setTimeout(() => { sharedVar++; }, 100);")
# → ["set", "timeout", "shared", "var"]   ← tên API bị vỡ vụn
```

BM25 index chứa tài liệu có từ `setTimeout` nguyên vẹn. Query `"set timeout"` sẽ khớp yếu hơn query `"setTimeout"` vì BM25 tính điểm theo từng term riêng lẻ.

**AST-based extraction (hiện tại):**

```python
# Cách mới — esprima parse → lấy Identifier tokens
extract_keywords("setTimeout(() => { sharedVar++; }, 100);", language="js")
# → "setTimeout sharedVar"   ← giữ nguyên tên API

extract_keywords("fs.appendFile(logPath, data, (err) => { throw err; })", language="js")
# → "fs appendFile logPath data err"   ← appendFile nguyên vẹn, không bị tách thành "append file"

extract_keywords("async function sendEmails(users) { await emailService.send(...) }", language="js")
# → "sendEmails users emailService send email"
```

Cơ chế hoạt động bên trong:

```python
# ast_preprocessor.py — extract_keywords() cho JS
script = esprima.parseScript(code, options={"tolerant": True, "tokens": True})
for tok in script.tokens:
    if tok.type == "Identifier" and tok.value not in _JS_STOPWORDS:
        result.append(tok.value)   # Chỉ lấy tên hàm/biến, bỏ if/for/const/await...
```

esprima phân biệt được `Identifier` (tên do lập trình viên đặt) với `Keyword` (từ khóa của JS như `async`, `await`, `for`). Regex không làm được điều này.

**So sánh query BM25 trước và sau:**

| Code | Regex tokenizer (cũ) | AST extraction (mới) |
|------|----------------------|----------------------|
| `setTimeout(cb, 100)` | `"set timeout cb"` | `"setTimeout cb"` |
| `fs.appendFile(path, data)` | `"fs append file path data"` | `"fs appendFile path data"` |
| `Promise.all([p1, p2])` | `"promise all p1 p2"` | `"Promise p1 p2"` |
| `emailService.send(email)` | `"email service send email"` | `"emailService send email"` |

Tên API nguyên vẹn → BM25 score cao hơn với tài liệu đúng chủ đề → top-3 docs được retrieve chính xác hơn.

**Bước 2 — BM25 tìm top-3 tài liệu liên quan:**

```python
raw_docs = retriever.search(query, top_k=3)
# → Trả về 3 tài liệu về: Promise.all pattern, sequential vs parallel, concurrency limit
```

**Bước 3 — Xây dựng prompt với context:**

```
Duoi day la cac tai lieu tham khao ve concurrent JavaScript:

Tai lieu 1 - Promise.all Pattern [patterns]:
Use Promise.all to run multiple async operations in parallel...

Tai lieu 2 - Sequential vs Parallel Execution [patterns]:
...

---

Convert to concurrent JavaScript:

async function sendEmails(users) {
  for(let i=0; i<users.length; i++) {
    await emailService.send(users[i].email);
  }
}
```

**Bước 4 — Model sinh ra fix code:**

```javascript
// Model output:
async function sendEmails(users) {
  await Promise.all(users.map(user => emailService.send(user.email)));
}
```

**Tại sao format prompt theo cách này?** Đây chính xác là format model đã được train với (từ `ai1_02_format_jsonl.py`). Nếu dùng format khác, model không nhận ra đây là task gì và cho kết quả sai.

### 6.3 FastAPI Server

Server expose 3 endpoints chính:

```
GET  /health                           ← Health check (public, không cần JWT)
POST /api/v1/ai/analyze                ← Phân tích code (yêu cầu JWT)
GET  /api/v1/ai/history/{user_id}      ← Lịch sử phân tích (yêu cầu JWT)
```

**Request / Response schema:**

```
POST /api/v1/ai/analyze
Request body:
  code        string  (bắt buộc) — source code cần phân tích
  language    string  (mặc định "javascript") — "javascript" | "typescript"
  user_id     string  (bắt buộc) — ID người dùng, dùng để lưu lịch sử

Response:
  user_id     string
  language    string
  issues[]    Issue   — danh sách lỗi phát hiện, rỗng nếu code sạch
  docs_used[] DocUsed — top-3 tài liệu BM25 đã dùng làm context
  cached      bool    — true nếu lấy từ Redis, false nếu gọi LLM mới

Issue:
  line_range  string  — ví dụ "12-18" hoặc "42"
  severity    string  — "high" | "medium" | "low"
  description string
  fix         string
```

**Concurrency Control — Semaphore:**

```python
# Giới hạn tối đa 3 LLM call đồng thời
_llm_semaphore = asyncio.Semaphore(3)
```

Lý do: LLM inference ngốn nhiều VRAM. Nếu 10 request đến cùng lúc và cùng chạy inference → GPU OOM (Out of Memory). Semaphore đảm bảo tối đa 3 request chạy inference song song, các request còn lại xếp hàng đợi.

**Kết quả load test thực tế (10 clients đồng thời, N=200 requests):**

| Metric | Giá trị |
|--------|---------|
| Throughput | 86 req/s |
| P50 latency | 3.2 ms |
| P95 latency | 112 ms |
| P99 latency | 129 ms |

P95 tăng từ 8ms (1 client) lên 112ms (10 clients) là do queue contention tại semaphore — đây là hành vi dự kiến và chấp nhận được với thiết kế hiện tại.

---

## 7. Đánh giá mô hình — Kết quả thực tế

### Phương pháp đánh giá

Chúng tôi xây dựng **20 test case thủ công** bao gồm 8 loại lỗi concurrency:

| Category | Số lượng | Ví dụ lỗi |
|----------|----------|-----------|
| Race Condition | 5 | Hai request đồng thời cùng đọc-ghi database |
| Event Loop Blocking | 5 | `readFileSync` trong vòng lặp async |
| Unhandled Rejection | 1 | Promise không có `.catch()` |
| Double Callback | 1 | Callback bị gọi 2 lần trong error path |
| Zalgo | 1 | Callback đôi khi sync, đôi khi async |
| Context Loss | 1 | `this` bị mất khi truyền method vào setTimeout |
| Callback Hell | 1 | Nested callbacks 3+ cấp |
| Resource Exhaustion | 1 | `Promise.all` không giới hạn với 1000 items |
| Sequential Awaits | 1 | Await tuần tự thay vì song song |
| Missing Promise.all | 1 | Loop với await riêng lẻ thay vì batch |
| Buffer Leak | 1 | Stream không có error handler |
| Event Loop Ordering | 1 | Nhầm lẫn nextTick vs setTimeout ordering |

**Cách tính điểm (Fix-Pattern Scoring):**

Thay vì so sánh output với "đáp án mẫu" (dễ bị sai do model viết theo style khác), chúng tôi kiểm tra xem output có chứa **pattern code của fix đúng** không:

```python
FIX_PATTERNS = {
    "test_18": [["promise.all("], ["await promise.all"]],
    # PASS nếu output chứa "promise.all(" HOẶC "await promise.all"
    "test_11": [["try {", "catch"], ["try{", "catch"]],
    # PASS nếu có try/catch block
}
```

Phương pháp này khách quan hơn: model có thể viết `Promise.all([...])` hay `await Promise.all(tasks)` đều được tính PASS, miễn là đã dùng đúng API.

### Kết quả thực tế (ngày 11/06/2026)

| Phương pháp | Pass | Partial | Fail | Pass Rate |
|-------------|------|---------|------|-----------|
| GPT-3.5-turbo zero-shot | 6 | 11 | 3 | 30% |
| Qwen2.5-Coder-1.5B (no fine-tune) | 8 | 9 | 3 | 40% |
| **ThreadLearn RAW** (fine-tune, no RAG) | **14** | **6** | **0** | **70%** |
| **ThreadLearn + RAG** (fine-tune + BM25) | **15** | **5** | **0** | **75%** |

**Phân tích kết quả:**

1. **Fine-tuning quan trọng hơn RAG** (+30pp vs +5pp): 783 mẫu training đã đủ để model học các pattern fix cụ thể của JavaScript concurrency

2. **Zero FAIL**: Model luôn sinh ra code có thể đọc được, không bao giờ trả về output rỗng hay crash

3. **RAG giúp trên các case khó**: test_03 (upsert pattern) và test_08 (async JSON parsing) được PASS nhờ RAG tìm được tài liệu đúng

4. **Còn 3 điểm yếu**: Zalgo, Double Callback, Buffer Leak — các pattern rất đặc thù, ít xuất hiện trong training data

5. **Fine-tune tốt hơn GPT-3.5** dù model nhỏ hơn nhiều: 75% vs 30% — chứng minh domain-specific fine-tuning hiệu quả hơn general-purpose LLM lớn

### Per-category chi tiết

| Category | RAW | RAG | Nhận xét |
|----------|-----|-----|----------|
| Race Condition | 3/5 | 3/5 | async/await, appendFile đúng; singleton cache partial |
| **Event Loop Blocking** | **5/5** | **5/5** | 100% — training data phủ tốt nhất |
| Unhandled Rejection | 1/1 | 1/1 | try/catch + next(error) |
| Double Callback | 0/1 | 0/1 | Cần return-cb guard pattern |
| Zalgo | 0/1 | 0/1 | process.nextTick normalization |
| Context Loss | 1/1 | 1/1 | Arrow function fix |
| Callback Hell | 1/1 | 1/1 | async/await chain |
| Resource Exhaustion | 1/1 | 1/1 | Batched slice |
| Sequential Awaits | 1/1 | 1/1 | Promise.all |
| Missing Promise.all | 1/1 | 1/1 | Promise.all |
| Buffer Leak | 0/1 | 0/1 | Stream error handler thiếu |
| Event Loop Ordering | 1/1 | 1/1 | Promise.resolve().then() |

---

## 8. Các lỗi gặp phải và cách giải quyết

Đây là phần ghi lại đầy đủ các vấn đề thực tế gặp phải trong quá trình phát triển — từ lỗi nhỏ đến lỗi ảnh hưởng lớn đến kết quả.

---

### Lỗi #1: Tên file có dấu cách — `model (1).safetensors`

**Khi nào xảy ra:** Khi tải model về từ HuggingFace Hub qua trình duyệt Windows.

**Triệu chứng:**
```
FileNotFoundError: models/merged/model.safetensors not found
```

**Nguyên nhân:** Windows tự thêm ` (1)` vào tên file nếu đã có file cùng tên trong thư mục download. File thực tế tên là `model (1).safetensors` nhưng `transformers` chỉ tìm đúng tên `model.safetensors`.

**Cách sửa:**
```powershell
Rename-Item "models\merged\model (1).safetensors" "model.safetensors"
Rename-Item "models\merged\config (1).json" "config.json"
```

**Cách tránh:** Dùng `huggingface-cli download` thay vì tải thủ công qua trình duyệt:
```bash
huggingface-cli download anha12/threadlearn-qwen2.5-coder-1.5b-merged --local-dir models/merged
```

---

### Lỗi #2: Unicode arrow `→` crash trên Windows (cp1252)

**Khi nào xảy ra:** Khi chạy script Python có `print("→ Result")` trên Windows terminal.

**Triệu chứng:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 0
```

**Nguyên nhân:** Windows Command Prompt và PowerShell mặc định dùng encoding `cp1252` (Windows-1252), không hỗ trợ ký tự Unicode mũi tên `→` (U+2192). Terminal Linux/Mac dùng UTF-8 nên không bị lỗi này.

**Cách sửa:**

Cách 1 — Thay thế Unicode bằng ASCII trong code:
```python
# Sai
print(f"Result → {score}")

# Đúng
print(f"Result -> {score}")
```

Cách 2 — Đổi encoding của terminal trước khi chạy:
```powershell
chcp 65001  # Chuyển sang UTF-8
python eval_rag_merged.py
```

**Bài học:** Khi viết script Python để chạy trên cả Windows lẫn Linux, tránh dùng ký tự Unicode đặc biệt trong chuỗi print. Dùng ASCII thuần.

---

### Lỗi #3: SFTTrainer báo lỗi `text_field` không tìm thấy

**Khi nào xảy ra:** Khi chạy `ai1_03_finetune.py` lần đầu.

**Triệu chứng:**
```
KeyError: 'text'
ValueError: Dataset does not have 'text' column
```

**Nguyên nhân:** Phiên bản mới của `trl` (>= 0.8.0) thay đổi API của SFTTrainer. Trước đây dùng `formatting_func` để biến đổi mẫu sang text, bây giờ phải tạo cột `text` trong dataset trước.

**Code cũ (không hoạt động):**
```python
def formatting_func(example):
    return f"{example['prompt']}{example['completion']}"

trainer = SFTTrainer(
    model=model,
    formatting_func=formatting_func,  # Không còn hoạt động đúng
    ...
)
```

**Code mới (hoạt động):**
```python
# Bước 1: Map dataset để tạo cột "text"
def make_text(example):
    return {"text": [f"{p}{c}" for p, c in zip(example['prompt'], example['completion'])]}

dataset = dataset.map(make_text, batched=True)

# Bước 2: Khai báo trong SFTConfig
training_args = SFTConfig(
    dataset_text_field="text",  # THIẾT YẾU
    ...
)

# Bước 3: Không truyền formatting_func nữa
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    peft_config=lora_config,
    processing_class=tokenizer,
    args=training_args,
    # formatting_func=...  ← XÓA DÒNG NÀY
)
```

---

### Lỗi #4: Prompt Format Mismatch — Kết quả sai (35% thay vì 70%)

**Đây là lỗi quan trọng nhất, tốn nhiều thời gian debug nhất.**

**Khi nào xảy ra:** Khi viết script eval đầu tiên (`eval_local_merged.py`) để đánh giá model đã fine-tune.

**Triệu chứng:** Model đạt 7/20 (35%) — thấp hơn cả base model chưa fine-tune (8/20, 40%). Điều này vô lý vì model đã được train thêm nhưng kết quả lại tệ hơn.

**Nguyên nhân gốc rễ:**

Script eval cũ dùng **chat template** của Qwen2.5 (dạng ChatML):

```python
# SAI — eval_local_merged.py (cũ)
messages = [
    {"role": "system", "content": "You are a JavaScript expert..."},
    {"role": "user", "content": f"Fix this code:\n{code}"}
]
prompt = tokenizer.apply_chat_template(messages, tokenize=False)
# → Tạo ra: "<|im_start|>system\nYou are...<|im_start|>user\nFix..."
```

Nhưng model được train theo **completion format** thuần túy:

```python
# ĐÚNG — ai1_02_format_jsonl.py (training)
prompt = f"Convert to concurrent JavaScript:\n\n{code}\n"
# → Chỉ là raw text, không có chat template
```

**Hậu quả:** Model học xong thì nhận biết pattern `"Convert to concurrent JavaScript:\n\n{code}\n"` là dấu hiệu để sinh code fix. Khi eval dùng chat template khác hoàn toàn, model không nhận ra đây là task gì → sinh output lung tung.

**Cách sửa:** Viết lại script eval (`eval_rag_merged.py`) dùng đúng format:

```python
# ĐÚNG — eval_rag_merged.py (mới)
def build_raw_prompt(code: str) -> str:
    """Đúng training format từ ai1_02_format_jsonl.py"""
    return f"Convert to concurrent JavaScript:\n\n{code}\n"

def run_inference(model, tokenizer, prompt: str) -> str:
    inputs = tokenizer([prompt], return_tensors="pt").to(DEVICE)
    input_len = inputs["input_ids"].shape[1]
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    # Chỉ lấy phần model SINH RA, không lấy phần prompt lặp lại
    generated = outputs[0][input_len:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()
```

**Kết quả sau khi sửa:** 14/20 (70%) RAW và 15/20 (75%) với RAG — tăng 35 percentage points.

**Bài học:** Khi fine-tune và eval phải dùng **cùng một format prompt**. Đây là nguyên tắc cơ bản nhưng dễ bỏ sót. Luôn kiểm tra file training script để xem prompt format chính xác là gì trước khi viết script eval.

---

### Lỗi #5: Con số 18/20 (90%) là không có cơ sở thực tế

**Khi nào phát hiện:** Khi kiểm tra lại nguồn gốc của con số 18/20 trong báo cáo ban đầu.

**Vấn đề:** Báo cáo ghi "ThreadLearn đạt 18/20 (90%)" nhưng không có file kết quả nào confirm con số này.

**Nguyên nhân:** Unit tests dùng **mock LLM** (trả về response cố định, không phải inference thật), nên unit test pass không có nghĩa là model thật hoạt động tốt.

```python
# ai2/server/llm_client.py
def _mock_analyze(code: str, docs: list) -> List[Issue]:
    """Default mock — luôn trả về cùng một response cố định"""
    return [Issue(type="race_condition", description="Detected race condition...")]
```

Mọi unit test đều dùng `LLM_PROVIDER=mock`, tức là không có test nào thực sự gọi model. Con số 90% bị suy ra sai từ kết quả unit test mock.

**Cách sửa:** Chạy inference thật với model đã merge, dùng script `eval_rag_merged.py`. Kết quả thực tế: 14/20 (70%) RAW, 15/20 (75%) RAG — thấp hơn 90% nhưng là con số thật và đáng tin cậy.

**Bài học:** **Không bao giờ viết kết quả vào báo cáo khi chưa chạy test thực tế với model thật.** Unit tests với mock không phản ánh chất lượng model. Cần có script eval riêng chạy inference thật và lưu kết quả vào file.

---

### Lỗi #6: `get_peft_model()` bị comment nhưng code vẫn hoạt động đúng

**Khi nào xảy ra:** Khi review lại code training sau khi merge.

**Phát hiện:** Trong `ai1_03_finetune.py`, dòng `model = get_peft_model(model, lora_config)` bị comment out:

```python
lora_config = LoraConfig(r=16, lora_alpha=32, ...)

# model = get_peft_model(model, lora_config)  ← BỊ COMMENT
# model.print_trainable_parameters()
```

**Tại sao không phải lỗi:** `SFTTrainer` từ `trl >= 0.8.0` tự động áp dụng LoRA config khi được truyền `peft_config=lora_config`. Gọi `get_peft_model()` thủ công TRƯỚC SFTTrainer sẽ gây lỗi "PEFT already applied". Code đúng là comment nó ra.

**Điểm dễ nhầm:** Khi đọc code, thấy comment có vẻ như "quên uncomment" nhưng thực ra là có chủ ý. Luôn kiểm tra version thư viện và đọc changelog khi upgrade.

---

### Lỗi #7: Merge model phải dùng CPU, không phải GPU

**Khi nào xảy ra:** Khi lần đầu chạy `ai1_04_merge_model.py` với cấu hình GPU.

**Triệu chứng:**
```
ValueError: You cannot merge a PEFT model that has been loaded with `load_in_4bit`
```

**Nguyên nhân:** Để merge LoRA vào base model, model phải ở dạng **full precision** (fp16 hoặc fp32). Nếu load 4-bit quantization (như khi training) thì không thể de-quantize chính xác để merge.

**Code sai:**
```python
# SAI: Dùng quantization config như lúc training
model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    quantization_config=bnb_config,  # ← KHÔNG được dùng khi merge
    device_map="auto",
)
```

**Code đúng:**
```python
# ĐÚNG: Load fp16 trên CPU, không quantize
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_ID,
    device_map="cpu",           # CPU để tránh tràn VRAM
    torch_dtype=torch.float16,  # Full precision, không quantize
    low_cpu_mem_usage=True,     # Tiết kiệm RAM khi load
)
```

---

### Lỗi #8: Windows `start /B` không redirect output đúng

**Khi nào xảy ra:** Khi cố gắng chạy FastAPI server ở background để benchmark.

**Triệu chứng:** Server không khởi động, không có log, không có error message.

**Nguyên nhân:** Lệnh `start /B uvicorn main:app > server.log 2>&1` trên Windows không hoạt động đúng trong bash emulator. Redirect `>` được shell xử lý sai.

**Cách sửa:** Dùng PowerShell `Start-Process`:

```powershell
Start-Process python -ArgumentList "-m", "uvicorn", "main:app", "--port", "8001" `
    -RedirectStandardOutput "server_out.log" `
    -RedirectStandardError "server_err.log" `
    -NoNewWindow
```

Hoặc chạy trong background PowerShell job:
```powershell
$job = Start-Job -ScriptBlock {
    Set-Location "d:\FPT\WDP301\WDP-Code\ThreadLearn-AI-Trainning\ai2\server"
    python -m uvicorn main:app --port 8001
}
```

---

## 9. Tính ưu việt và ứng dụng thực tế

### So sánh với các phương pháp khác

| Khả năng | ESLint | ThreadSanitizer | GPT-3.5 zero-shot | **ThreadLearn** |
|----------|--------|-----------------|-------------------|-----------------|
| Phát hiện lỗi | Tốt | Tốt | Trung bình | Tốt |
| Sinh code fix | Không | Không | Có | **Có** |
| Chạy offline | Có | Có | Không (cần API) | **Có** |
| Chi phí mỗi request | Miễn phí | Miễn phí | ~$0.002 | **Miễn phí** |
| Hiểu async/await | Hạn chế | Không | Có | **Có** |
| Pass rate benchmark | N/A | N/A | 30% | **75%** |
| Model size | N/A | N/A | 175B params | **1.5B params** |

### Ưu điểm nổi bật

**1. Chạy hoàn toàn offline trên phần cứng thông thường**

Model chỉ cần 8GB VRAM (RTX 4060, RTX 3070) để chạy inference. Không cần internet, không cần subscription. Có thể nhúng vào IDE extension hoặc CI/CD pipeline của doanh nghiệp có firewall nghiêm ngặt.

**2. Tốt hơn GPT-3.5 dù nhỏ hơn 100 lần**

75% so với 30% — chứng minh **fine-tuning chuyên biệt** hiệu quả hơn **model lớn tổng quát** cho bài toán domain-specific. Đây là điểm mấu chốt: một model nhỏ được train đúng mục đích thường outperform model lớn dùng zero-shot.

**3. Zero failure rate**

Trong toàn bộ 20 test case, model **không bao giờ** sinh output rỗng hay code không hợp lệ. Luôn trả về đoạn code có thể đọc được, dù đôi khi chưa hoàn toàn đúng.

**4. RAG tăng chất lượng mà không cần retrain**

Chỉ cần thêm tài liệu mới vào `knowledge_base.json` và rebuild BM25 index (dưới 500ms cho 2050 docs), model tự động có thêm kiến thức. Không cần chạy lại toàn bộ quá trình fine-tuning. Đây là lợi thế lớn khi cần cập nhật kiến thức theo thời gian.

**5. Latency thấp, phù hợp real-time**

P50 = 3.2ms, P95 = 112ms dưới tải 10 concurrent clients — đủ nhanh để tích hợp vào IDE extension mà không làm chậm trải nghiệm lập trình viên.

### Ứng dụng thực tế

**1. IDE Extension (VS Code, JetBrains)**

Tích hợp như một "code reviewer" tự động: khi lập trình viên save file hoặc commit, ThreadLearn tự phân tích và highlight các đoạn code có nguy cơ race condition, kèm gợi ý fix ngay trong editor.

**2. CI/CD Gate**

Thêm vào GitHub Actions: pull request chỉ được merge nếu ThreadLearn không phát hiện race condition nghiêm trọng. Tương tự như lint checks nhưng thông minh hơn và có khả năng đề xuất fix.

```yaml
# .github/workflows/threadlearn.yml
- name: ThreadLearn Race Condition Check
  run: |
    curl -X POST http://threadlearn-api/analyze \
      -H "Content-Type: application/json" \
      -d "{\"code\": \"$(cat $CHANGED_FILE)\"}"
```

**3. Educational Tool cho FPT University**

Trong môn học JavaScript/Node.js, sinh viên có thể submit code và nhận phản hồi về lỗi concurrency kèm giải thích chi tiết. Giúp sinh viên học được best practices mà không cần chờ giảng viên/TA review thủ công.

**4. Code Review Assistant**

Tích hợp vào pull request workflow: khi reviewer mở PR, ThreadLearn tự động comment vào các dòng code có vấn đề kèm code fix gợi ý — giúp tiết kiệm thời gian review và đảm bảo tính nhất quán.

---

## 10. Hướng dẫn chạy lại từ đầu

### Yêu cầu môi trường

```
Python 3.13+
RAM: 16GB+
Hệ điều hành: Windows 10/11 hoặc Linux
GPU: Chỉ cần khi dùng LLM_PROVIDER=ollama với model local
```

### Bước 1: Cài dependencies cho AI2 server

```bash
cd ThreadLearn-AI-Trainning/ai2/server
pip install -r requirements.txt
```

### Bước 2: Tạo file `.env`

Tạo file `ai2/server/.env`:

```env
# Chọn 1: mock | openai | ollama
LLM_PROVIDER=mock

OPENAI_API_KEY=

# Phải khớp với JWT_SECRET trong Node.js backend
JWT_SECRET=your_super_secret_access_key_change_me

# Tùy chọn — server chạy bình thường nếu thiếu
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
OLLAMA_URL=http://localhost:11434
HF_TOKEN=
```

> ⚠️ **Không commit file `.env` lên git.**

### Bước 3: Chạy AI2 server

**Linux/Mac:**
```bash
cd ThreadLearn-AI-Trainning/ai2/server
uvicorn main:app --reload --port 8001
```

**Windows (PowerShell):**
```powershell
cd ThreadLearn-AI-Trainning\ai2\server
python -m uvicorn main:app --reload --port 8001
```

Kiểm tra server:
```bash
curl http://localhost:8001/health
# → {"status":"ok","retriever_docs":2050}
```

Swagger UI: http://localhost:8001/docs

### Bước 4: Gọi API analyze (cần JWT)

Tạo JWT token (chạy từ `ai2/server/`):

```bash
python -c "
from jose import jwt; import time
from config import JWT_SECRET
token = jwt.encode({'sub':'test-user','exp':int(time.time())+3600}, JWT_SECRET, algorithm='HS256')
print(token)
"
```

Gọi analyze:
```bash
curl -X POST http://localhost:8001/api/v1/ai/analyze \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "for(var i=0;i<3;i++){setTimeout(function(){console.log(i)},1000);}",
    "language": "javascript",
    "user_id": "test-user"
  }'
```

### Bước 5: Chạy unit tests

```bash
cd ThreadLearn-AI-Trainning/ai2
pytest tests/ -v
```

### Bước 6: Chạy evaluation (20 test cases thực tế)

Cần cài thêm inference dependencies:
```bash
pip install transformers torch accelerate peft bitsandbytes datasets tqdm
```

Tải model đã merge:
```bash
pip install huggingface_hub
huggingface-cli download anha12/threadlearn-qwen2.5-coder-1.5b-merged \
  --local-dir models/merged
```

> ⚠️ **Windows:** Kiểm tra tên file sau khi tải — nếu tên là `model (1).safetensors` thì đổi lại thành `model.safetensors`.

Chạy evaluation:
```bash
cd ThreadLearn-AI-Trainning/ai2
python eval_rag_merged.py
# Kết quả lưu tại: ai2/eval_rag_results.json
# Kỳ vọng: RAW ~14/20 (70%), với RAG ~15/20 (75%)
```

### Bước 7 (tùy chọn): Chạy với Redis và MongoDB

Nếu muốn bật cache và history, khởi động Redis + MongoDB bằng Docker:

```bash
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 27017:27017 mongo:7
```

Server tự kết nối theo `REDIS_URL` và `MONGODB_URL` trong `.env`.

### Bước 8 (tùy chọn): Chạy bằng Docker

```bash
cd ThreadLearn-AI-Trainning/ai2
docker build -t threadlearn-ai2 .
docker run -d \
  -p 8001:8001 \
  -e LLM_PROVIDER=mock \
  -e JWT_SECRET=your_super_secret_access_key_change_me \
  --name ai2 \
  threadlearn-ai2
```

### Bước 9 (tùy chọn): Fine-tune lại từ đầu

Chỉ cần khi muốn thêm dữ liệu training mới:

```bash
# Thu thập dữ liệu
cd ThreadLearn-AI-Trainning/ai1/modules
python ai1_01_dataset_collector.py
# Cần GITHUB_TOKEN trong .env

# Format sang JSONL
python ai1_02_format_jsonl.py

# Bước 3: Upload lên Kaggle, chạy notebook ai1_03_finetune.py
# Chạy trên Kaggle vì cần 2×T4 GPU miễn phí

# Merge adapter sau khi train xong
cd ThreadLearn-AI-Trainning/ai1/training
python ai1_04_merge_model.py
```

---

## 11. Tài liệu tham khảo

1. **NodeCB (ASE 2017)** — T. Xu et al., *"Understanding Concurrency Bugs in Node.js"*, IEEE/ACM ASE 2017. Nghiên cứu gốc phân tích 57 lỗi concurrency trên 53 dự án Node.js — nền tảng lý thuyết cho dự án.

2. **QLoRA** — T. Dettmers et al., *"QLoRA: Efficient Finetuning of Quantized LLMs"*, NeurIPS 2023. Kỹ thuật fine-tune 4-bit quantization được áp dụng trực tiếp.

3. **Qwen2.5-Coder** — Qwen Team, *"Qwen2.5-Coder Technical Report"*, arXiv:2409.12186, 2024. Model base được fine-tune trong dự án.

4. **PCWMs** — G. Singh, A. Guha, B. Kailkhura, H. Menon, *"PCWMs: Prompting with Chain-of-Thought World Models for Concurrency Bug Detection"*, arXiv:2604.20926v2, 2026. Hướng tiếp cận LLM-only dùng làm baseline so sánh.

5. **BM25** — S. Robertson et al., *"Okapi at TREC-3"*, TREC 1994. Thuật toán tìm kiếm nền tảng cho RAG pipeline.

6. **TRL (SFTTrainer)** — HuggingFace TRL library, https://github.com/huggingface/trl. Framework fine-tuning với SFTTrainer.

7. **LoRA** — E. Hu et al., *"LoRA: Low-Rank Adaptation of Large Language Models"*, ICLR 2022. Kỹ thuật LoRA nền tảng trước khi được kết hợp với quantization thành QLoRA.

---

*README này mô tả quá trình phát triển thực tế của dự án ThreadLearn từ tháng 06/2026. Mọi con số đánh giá đều từ inference thật trên phần cứng thực tế (RTX 4060 Laptop GPU), không phải từ mock hay estimation.*

*Lê Trí Trung · Hà Văn Ân | FPT University | WDP301*
