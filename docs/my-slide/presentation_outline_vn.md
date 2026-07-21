# 🎯 KỊCH BẢN THUYẾT TRÌNH THREADLEARN (Tiếng Việt)

---

## PHẦN 1 — NỖI ĐAU (Vấn đề & Động lực) ⏱ ~2 phút

### 1.1. JavaScript concurrency bugs — ai cũng gặp, ít ai để ý

> **Người nói:** Cho cả nhóm thấy đây là vấn đề THỰC TẾ, không phải chuyện sách vở.

| Điểm cần nhấn | Dẫn chứng |
|--------------|-----------|
| JS chạy single-threaded event loop, nhưng async code gây ra concurrency bugs | 93% lỗi thực tế gây crash/hỏng dữ liệu/treo server (NodeCB, ASE 2017) |
| Ví dụ trực quan: **Race condition bán hàng** — 2 user cùng mua sản phẩm cuối cùng, cả 2 đều thấy "còn 1", cả 2 đều mua được → kho âm | Dùng slide code before/after |
| Dev không nhận ra vì test đơn lẻ luôn PASS, chỉ fail khi có nhiều user thật | Demo 1 slide "code chạy 1 mình: OK / 1000 users: CHẾT" |

### 1.2. Công cụ hiện tại bất lực

| Công cụ | Phát hiện lỗi? | Tự sửa? | Chạy offline? |
|---------|:---:|:---:|:---:|
| ESLint | ✅ Có | ❌ Không | ✅ |
| GPT-3.5/4 | ⚠️ 30% | ✅ Có | ❌ Cần API + $ |
| **ThreadLearn** | ✅ | ✅ | ✅ Miễn phí |

> **Cầu nối sang Trung:** "Vậy để xây dựng một hệ thống AI làm được cả 3 việc — vừa phát hiện, vừa sửa, vừa chạy offline — chúng em chia làm 2 phần..."

---

## PHẦN 2 — TRUNG (AI2) ⏱ ~5 phút

> **Trung:** "Em phụ trách toàn bộ hệ thống **serving** — nhận code từ user, phân tích, trả kết quả. Gồm 3 khối chính."

### 2.1. Knowledge Base + BM25 Search Engine

```
2050 tài liệu JavaScript concurrency
           │
           ▼
    BM25 Index (load RAM, <500ms)
           │
           ▼
  Tìm top-3 tài liệu liên quan nhất → nhét vào prompt cho LLM
```

| Điểm nhấn kỹ thuật | Chi tiết |
|-------------------|----------|
| **Tại sao BM25 mà không phải Vector Search?** | Không cần GPU, không cần embed model, keyword search khớp chính xác tên API (`setTimeout`, `Promise.all`) |
| **CamelCase-aware Tokenizer** | `fetchAllUsers` → `["fetch", "all", "users"]`, `appendFile` giữ nguyên không bị tách thành `append file` |
| **Auto-stopwords** | Tự động tính IDF loại bỏ từ phổ biến khi scale lên 5000+ docs |

### 2.2. Race Condition Detector (Static Analysis)

```
10 patterns × (JS + Python)
├── JS:  closure_loop_var, shared_var_settimeout, promise_no_await, concurrent_write_array, counter_no_atomic
└── Python: global_var_thread, shared_list_no_lock, thread_read_write_race, missing_join, singleton_lazy_init
```

| Điểm nhấn | |
|----------|-----|
| Rule-based trên AST nodes — **nhanh, không cần LLM** | |
| Tích hợp `ast_preprocessor.py` từ AI1 (Ân) — dùng chung module | |
| Dedup + false-positive suppression (có Lock → không flag) | |

### 2.3. FastAPI Server + RAG Pipeline

```
┌─────────────────────────────────────────────────────┐
│  POST /api/v1/ai/analyze  {code, language}          │
│         │                                           │
│         ├─► JWT Verify (Node.js backend)            │
│         ├─► Redis Cache? ── HIT ──► return ngay     │
│         ├─► AST Extract Keywords (esprima)          │
│         ├─► BM25 Search top-3 docs                  │
│         ├─► Build Prompt = docs + code              │
│         ├─► LLM Inference (Semaphore max 3)         │
│         ├─► Race Detector scan                      │
│         ├─► Format JSON Response                    │
│         ├─► Save MongoDB (history)                  │
│         └─► Set Redis (TTL 24h)                     │
└─────────────────────────────────────────────────────┘
```

| Infrastructure | |
|---------------|-----|
| **Redis Cache** | SHA256(code+language), TTL 24h, graceful degradation |
| **MongoDB History** | Motor async, phân trang `/history/{user_id}?page=1&limit=20` |
| **Concurrency Control** | `asyncio.Semaphore(3)` — tránh GPU OOM |
| **Docker Compose** | FastAPI + Redis + MongoDB + Ollama |

| Kết quả Load Test | |
|-------------------|---|
| Throughput | **86 req/s** |
| P50 latency | **3.2 ms** |
| P95 latency | **112 ms** |

### 2.4. Điểm khó & cách vượt qua (Trung)

| Vấn đề | Cách giải quyết |
|--------|----------------|
| FE team (Đạt) bị block vì chưa có API | Ship Mock LLM sớm (CP3) → FE unblock, thay LLM thật sau |
| GPU OOM khi nhiều request đồng thời | Semaphore(3) + queue tự động |
| Redis/MongoDB không available | Graceful degradation — server không crash |
| Prompt format mismatch giữa train và inference | Phối hợp với Ân debug → viết lại eval script đúng format |

> **Cầu nối sang Ân:** "Hệ thống serving đã sẵn sàng, nhưng cần một con model đủ mạnh để thực sự HIỂU và SỬA được lỗi concurrency — đó là phần của Ân."

---

## PHẦN 3 — ÂN (AI1) ⏱ ~5 phút

> **Ân:** "Em phụ trách phần **trái tim** của hệ thống — con model AI. Nhiệm vụ: dạy một model 1.5B tham số hiểu và sửa được lỗi concurrency JavaScript."

### 3.1. Dataset — Garbage In, Garbage Out

```
Nguồn dữ liệu:
├── GitHub Code Search (15 query patterns) → lọc commit thật
├── Synthetic Pairs (60 cặp viết tay, 8 category)
└── Data Augmentation (100 mẫu cho pattern yếu)

Kết quả: 783 cặp (code lỗi → code đã sửa)
         Train 90% (704) / Eval 10% (79)
         Shuffle seed=42 (tái hiện được)
```

| Điểm nhấn | |
|-----------|-----|
| **Tại sao completion format, không phải chat format?** | Task là "thấy code → sinh code fix", không phải hội thoại. Dùng sai format → pass rate giảm từ 70% còn 35% |
| **AST làm sạch dữ liệu** | Dùng `@babel/parser` chuẩn hóa code, xóa comment rác, giữ nguyên tên API |
| **Data Augmentation** | 100 mẫu synthetic cho 4 pattern critical + 9 mẫu targeted cho 5 pattern yếu |

### 3.2. QLoRA Fine-tuning — Tiết kiệm 8 lần VRAM

```
Model gốc Qwen2.5-Coder-1.5B (3GB float16)
    ↓ Load 4-bit quantization (NF4) → ~800MB VRAM
    ↓ Thêm LoRA adapter (r=16) → chỉ train 0.5% tham số
    ↓ Train trên Kaggle (2× T4 GPU, miễn phí)
    ↓ ~500 steps, ~2 giờ
    ↓ Merge adapter vào base → Model hoàn chỉnh 3GB
```

| Cấu hình | Giá trị | Ý nghĩa |
|----------|--------|---------|
| `r=16, alpha=32` | Cân bằng hiệu quả / bộ nhớ |
| `4-bit NF4 + Double Quant` | VRAM: 12GB → 4GB |
| `gradient_accumulation=8` | "Giả lập" batch size 8 với 1 sample/lần |
| `lr=2e-4, cosine decay` | Học nhanh đầu, mịn cuối |
| `max_steps=500` | Tránh overfit trên dataset nhỏ |

### 3.3. Lesson Learned — Những bài học xương máu

| # | Lỗi | Hậu quả | Cách sửa |
|---|-----|---------|----------|
| 1 | Tên file Windows `model (1).safetensors` | Model không load được | Dùng `huggingface-cli download` |
| 2 | Unicode `→` crash trên Windows cp1252 | Script eval không chạy | Dùng ASCII `->` hoặc `chcp 65001` |
| 3 | SFTTrainer API thay đổi (`text_field`) | Không train được | Map dataset tạo cột `"text"` |
| **4** | **Prompt Format Mismatch** | **Pass rate 35% thay vì 70%** | **Dùng cùng format train/eval** |
| 5 | Con số 18/20 (90%) từ mock, không phải thật | Báo cáo sai | Luôn chạy inference thật trước khi viết báo cáo |
| 6 | `get_peft_model()` bị comment | Tưởng lỗi, thực ra SFTTrainer mới tự apply | Đọc changelog khi upgrade lib |
| 7 | Merge model phải dùng CPU fp16 | Không merge được trên GPU 4-bit | `device_map="cpu"` + `torch.float16` |

### 3.4. Kết quả — Con số biết nói

| Phương pháp | Pass Rate |
|-------------|-----------|
| GPT-3.5-turbo zero-shot | **30%** |
| Qwen2.5-Coder-1.5B (no fine-tune) | 40% |
| **ThreadLearn RAW** (fine-tune, no RAG) | **70%** |
| **ThreadLearn + RAG** (fine-tune + BM25) | **75%** 🏆 |

| Real-world 30-case (production npm bugs) | |
|------------------------------------------|-----|
| Base model (no fine-tune) | 60% |
| Merged v1 + pipeline | **73.3%** 🏆 |
| GPT-3.5-turbo + pipeline | 65% |

> **Takeaway:** Model 1.5B fine-tune chuyên biệt **vượt GPT-3.5** (175B) dù nhỏ hơn **~125 lần**. Domain-specific fine-tuning > general-purpose LLM.

---

## PHẦN 4 — TỔNG KẾT ⏱ ~1 phút

> **Cả 2 cùng đứng nói xen kẽ:**

| Người | Điểm nhấn |
|-------|-----------|
| **Trung** | "Hệ thống serving hoàn chỉnh: RAG pipeline + cache + history + load test. Chạy offline, miễn phí, P95 = 112ms." |
| **Ân** | "Model 1.5B vượt GPT-3.5. Bí quyết: dataset sạch + QLoRA hiệu quả + đúng format prompt." |
| **Cả 2** | "ThreadLearn = Fine-tuned LLM + RAG Pipeline → Phát hiện & sửa lỗi concurrency JS, chạy hoàn toàn offline trên laptop 8GB VRAM." |

### Ứng dụng thực tế (1 slide cuối)

```
📌 IDE Extension (VS Code) → highlight lỗi khi save file
📌 CI/CD Gate (GitHub Actions) → chặn PR có race condition
📌 Educational Tool (FPT University) → review code tự động
📌 Code Review Assistant → comment fix suggestion trên PR
```

---

## 📋 PHỤ LỤC: Phân chia slide đề xuất

| Slide | Người nói | Nội dung |
|-------|-----------|----------|
| 1 | Chung | Title + Team |
| 2 | Chung | Nỗi đau: JS concurrency bugs + ví dụ race condition |
| 3 | Chung | Công cụ hiện tại bất lực → ThreadLearn giải quyết gì |
| 4 | Chung | Kiến trúc tổng thể (diagram) |
| 5 | Trung | Knowledge Base + BM25 |
| 6 | Trung | Race Condition Detector (10 patterns) |
| 7 | Trung | FastAPI Server + RAG Pipeline flow |
| 8 | Trung | Infrastructure: Redis, MongoDB, Docker, Load Test |
| 9 | Ân | Dataset: nguồn, format, con số |
| 10 | Ân | QLoRA Fine-tuning: cấu hình, tại sao chọn |
| 11 | Ân | Lessons Learned — 7 lỗi + cách sửa |
| 12 | Ân | Kết quả: Bảng Pass Rate + Real-world benchmark |
| 13 | Chung | Ứng dụng thực tế + Kết luận |
 
