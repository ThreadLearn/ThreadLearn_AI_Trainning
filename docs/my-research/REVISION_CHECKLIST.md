# Checklist Chỉnh Sửa Paper — ThreadLearn v3

Dựa trên nhận xét hội đồng (`nhan_xet_logic_ThreadLearn.docx`). Mục tiêu: 6.5/10 → 7.5–8/10.

---

## Nhóm A — Cao (bắt buộc, tránh bị phản biện)

- [x] **A1** — Xóa claim "~125× fewer parameters" (GPT-3.5-turbo chưa công bố param)
  - Abstract: `despite ~125× fewer parameters` → `despite using a much smaller open-weight 1.5B model`
  - Section 6: `~125x fewer parameters` → `using a much smaller open-weight 1.5B model`
  - Conclusion: tương tự

- [x] **A2** — Hạ claim "fixes bugs" → "generates fix suggestions"
  - Abstract: `generate fixes` → `generate fix-pattern suggestions`
  - Section 6 + Conclusion: nhất quán wording
  - Table 1 cột "Fix": giữ ✓ nhưng thêm footnote "fix suggestion"

- [x] **A3** — Sửa RQ2: không thể quy kết improvement cho riêng BM25 khi pipeline gồm nhiều thành phần
  - Section 1 RQ2: `Does BM25+AST retrieval benefit every model equally...` → `Does the full static-analysis and retrieval-augmented pipeline improve fix suggestion quality equally across models, or does its benefit depend on prior fine-tuning?`
  - Section 6 answering RQ2: đổi "retrieval only helps" → "the full pipeline only helps"

- [x] **A4** — Hedging benchmark 30 case: thêm Threats to Validity
  - Abstract + Sec 6 + Conclusion: `beats GPT-3.5-turbo` → `shows a higher score than GPT-3.5-turbo on our 30-case preliminary benchmark`
  - Cuối Section 5: thêm subsection **Threats to Validity** (~3 câu):
    > "The 30-case benchmark is small; score differences of 2–3 cases (≈7 pp) are not statistically significant without formal testing (e.g., McNemar's test). Results should be interpreted as preliminary evidence on this benchmark, not as a claim of general superiority."

- [x] **A5** — Làm rõ mâu thuẫn dataset: "no model-generated labels" vs "reasoning trace by teacher model"
  - Section 4.1: `built entirely by the authors with no crowdsourcing or model-generated labels`
  - → `built entirely by the authors with no crowdsourcing; fix labels are human-verified, and reasoning traces were produced with teacher-model assistance and manually reviewed`

- [x] **A6** — Thêm bảng mapping: 5 detector patterns ↔ 10 benchmark categories
  - Thêm vào cuối Section 4.2 (sau mô tả Static Detector):
  
  | Benchmark Category | Detector Pattern | Fix Pattern | Support Level |
  |---|---|---|---|
  | Race Condition | `counter_no_atomic`, `concurrent_write_array` | mutex, atomic update | Direct |
  | Unhandled Rejection | `promise_no_await` | await, try/catch, .catch() | Direct |
  | Sequential Awaits | `promise_no_await` | Promise.all, batching | Direct |
  | Closure Loop Var | `closure_loop_var` | var→let | Direct |
  | Shared Var setTimeout | `shared_var_settimeout` | scoped variable | Direct |
  | Double Callback | callback guard heuristic | called-flag, early return | Partial |
  | Resource Exhaustion | resource-loop heuristic | concurrency limit, pool | Partial |
  | Event Loop Blocking | sync-call heuristic | async alternative, worker | Partial |
  | Zalgo | none | force async boundary | Indirect (RAG only) |
  | Context Loss | none | bind, arrow fn, AsyncLocalStorage | Indirect (RAG only) |
  | Stream Leak | none | close/destroy, finally | Indirect (RAG only) |
  | Callback Hell | none | Promise/async-await refactor | Indirect (RAG only) |

- [x] **A7** — Bỏ claim "first" tuyệt đối
  - Conclusion: `It is the first end-to-end system...` → `To the best of our knowledge, ThreadLearn is among the first attempts to combine...`

---

## Nhóm B — Trung bình (nên sửa, tăng điểm rõ)

- [x] **B1** — Di chuyển Evaluation Metrics sang Section 5
  - Hiện tại nằm trong Section 4.2 (Architecture) — không đúng chỗ
  - Tạo subsection `5.1 Evaluation Metrics` với định nghĩa rõ:
    - PASS = output contains expected fix pattern AND syntactically valid code
    - PARTIAL = syntactically valid code generated, but without expected fix pattern
    - FAIL = no code generated
  - Thêm: "We acknowledge PASS/PARTIAL/FAIL is a proxy metric; behavioral correctness via unit test pass rate is left for future work."

- [x] **B2** — Chia Related Work thành 4 nhóm rõ
  - Hiện 1 đoạn gom tất cả
  - Cấu trúc mới:
    1. **Static and dynamic bug detectors** (ThreadSanitizer, ESLint, NodeCB, NACD)
    2. **LLMs for code repair** (PCWMs, general code LLMs)
    3. **Retrieval-augmented generation for code** (Lewis et al. RAG)
    4. **Fine-tuning for code tasks** (QLoRA, LoRA, domain SFT)
  - Cuối mỗi nhóm: 1 câu nêu gap → dẫn đến ThreadLearn

- [x] **B3** — Liên kết latency với implication thực tế
  - Thêm 1 câu trong Section 6: "The higher inference latency (≈26s vs ≈1.8s for GPT-3.5-turbo API) positions ThreadLearn for offline code review and IDE-assisted repair workflows, not real-time production monitoring."

---

## Nhóm C — Nhỏ (polish, +0.2–0.3 điểm)

- [x] **C1** — Thêm caveat metric trong Section 5
  - Sau bảng kết quả: "We note this metric rewards identifying the correct fix class; a model could score PASS while introducing a semantically different solution. Validating behavioral correctness via automated test suites is future work."

- [x] **C2** — Nhất quán terminology
  - `BM25+AST retrieval` khi nói component riêng lẻ
  - `static-analysis and retrieval-augmented pipeline` khi nói full pipeline
  - Không trộn lẫn trong cùng một câu

- [x] **C3** — Sửa claim nhỏ trong Related Work / Table 1
  - `ThreadLearn is the only entry combining all four` → `ThreadLearn combines all four`

---

## Thứ tự thực hiện

| # | Việc | Nhóm | File |
|---|---|---|---|
| 1 | Tạo checklist (file này) | — | `REVISION_CHECKLIST.md` |
| 2 | Sửa Abstract: A1 + A2 + A4 | A | `build_docx_v3.py` |
| 3 | Sửa Section 1 RQ2: A3 | A | `build_docx_v3.py` |
| 4 | Sửa Section 4.1 dataset wording: A5 | A | `build_docx_v3.py` |
| 5 | Sửa Section 4.2 + thêm mapping table: A6 + B1 | A+B | `build_docx_v3.py` |
| 6 | Sửa Related Work → 4 nhóm: B2 | B | `build_docx_v3.py` |
| 7 | Sửa Section 5: thêm Threats to Validity + caveat: A4 + C1 | A+C | `build_docx_v3.py` |
| 8 | Sửa Section 6: A3 + A1 + B3 | A+B | `build_docx_v3.py` |
| 9 | Sửa Conclusion: A1 + A2 + A7 | A | `build_docx_v3.py` |
| 10 | Nhất quán C2 + C3 toàn paper | C | `build_docx_v3.py` |
| 11 | Export `Trung_ThreadLearn_v3.docx` | — | python run |
| 12 | Verify nội dung v3 | — | manual check |

---

*Tạo: 2026-07-04. Target: 7.5–8/10 theo thang điểm hội đồng.*
