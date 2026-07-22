# CV Entry — ThreadLearn (theo format template hiện có)

---

## Bản chính — dùng cho mục "Research / Project"

**ThreadLearn: AI Race-Condition Detector & Fix Suggestion Engine**
06/2026 – 07/2026
AI Engineer — RAG Pipeline, FastAPI Server, Static Analysis

- Built and fine-tuned a **1.5B-parameter LLM** (Qwen2.5-Coder + **QLoRA**) that outperforms **GPT-3.5-turbo** at detecting and fixing JavaScript concurrency bugs — validated on 30 real production bugs, scoring **73.3%** vs GPT-3.5's 65.0%, despite using a ~125× smaller open-weight model.
- Designed a **RAG retrieval pipeline** (BM25 + AST-based keyword extraction over a 2,050-document knowledge base) combined with a custom static race-condition detector (14 rule-based patterns), reducing what the LLM needs to infer and cutting hallucinated fixes.
- Shipped a production **FastAPI microservice** (JWT auth, Redis caching, MongoDB history, async concurrency control) serving real-time fix suggestions — co-authored a research paper submitted to **ICTA 2026** (double-blind peer review).

GitHub: https://github.com/[your-org]/ThreadLearn-AI-Trainning

---

## Bản rút gọn — nếu CV giới hạn 3 dòng

**ThreadLearn — AI Concurrency Bug Detector**
06/2026 – 07/2026 · AI Engineer
Fine-tuned a 1.5B LLM (QLoRA + RAG) that beat GPT-3.5-turbo (73.3% vs 65.0%) at fixing real JavaScript race conditions from production npm packages; built the full RAG pipeline (BM25 + AST) and FastAPI serving layer; co-authored paper submitted to ICTA 2026.

---

## Bản tiếng Việt (nếu CV song ngữ)

**ThreadLearn — Hệ thống AI phát hiện & sửa lỗi Concurrency JavaScript**
06/2026 – 07/2026 · AI Engineer — RAG Pipeline & Backend Server

- Fine-tune mô hình ngôn ngữ **1.5B tham số** (Qwen2.5-Coder + **QLoRA**) vượt qua **GPT-3.5-turbo** trong việc phát hiện và đề xuất fix lỗi concurrency JavaScript — đạt **73.3%** trên 30 bug thật lấy từ package npm production, so với 65.0% của GPT-3.5, dù dùng model nhỏ hơn ~125 lần.
- Thiết kế **pipeline RAG** (BM25 retrieval + trích xuất từ khóa bằng AST) trên kho tri thức 2.050 tài liệu, kết hợp bộ phát hiện race condition tĩnh tự viết (14 pattern), giúp giảm hallucination khi model sinh fix.
- Triển khai **FastAPI microservice** production-ready (JWT auth, Redis cache, MongoDB, kiểm soát concurrency) — đồng tác giả bài báo nghiên cứu nộp **ICTA 2026** (double-blind peer review).

GitHub: https://github.com/[your-org]/ThreadLearn-AI-Trainning

---

## Ghi chú khi điền vào CV thật

1. **Thay `[your-org]`** bằng link GitHub repo thật của bạn (giống format `Git Hub: https://...` trong template mẫu).
2. **Số liệu 73.3% / 65.0% / 1.5B / 125× / 2,050 docs / 30 bugs / 14 pattern** — đều lấy trực tiếp từ `docs/RESEARCH_LOG.md` và paper `Trung_ThreadLearn_v4_blind.docx` đã verify, không phải ước lượng. An toàn để đưa vào phỏng vấn, nhà tuyển dụng hỏi sâu vẫn giải thích được.
3. Nếu recruiter không phải dân AI/ML, có thể đơn giản hóa từ "QLoRA fine-tuning" → "fine-tuned a small AI model" và "RAG pipeline" → "AI search system" — giữ số liệu %, giữ tên GPT-3.5 (ai cũng biết).
4. Role đặt là **"AI Engineer"** (khớp phần bạn phụ trách: AI2 — RAG, server, detector) — không ghi "Data Scientist" hay "ML Researcher" vì không khớp công việc thực tế đã làm.
5. **Đừng ghi "90% pass rate"** — số đó đã bị xác nhận sai (từ mock LLM, không phải kết quả thật). Chỉ dùng 73.3%/65.0% từ benchmark 30-case chính thức.
