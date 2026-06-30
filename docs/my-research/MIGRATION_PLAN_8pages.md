# Kế hoạch rút gọn ThreadLearn paper xuống < 8 trang

**File mục tiêu:** `threadlearn_paper.tex` (LNCS, `llncs.cls`, runningheads)
**Độ dài hiện tại:** ~16 trang (diagnostics báo page 15+ trước bibliography; bib chiếm thêm ~2 trang)
**Mục tiêu:** nội dung chính (intro → conclusion) gọn trong giới hạn, tổng < 8 trang kể cả refs nếu venue tính refs, hoặc < 8 trang nội dung nếu refs không tính.
**Mức cắt cần đạt:** ~50% diện tích.

> ⚠️ LNCS thường tính references vào page limit. Plan này giả định **refs CÓ tính** (case khó nhất). Nếu venue không tính refs, phần bib khỏi cắt — nới được ~2 trang.

---

## 0. Nguyên tắc khi cắt

- **Không xóa claim/số liệu cốt lõi.** Giữ: 73.3% main result, +13.3pp, 125× ít params, 3 RQ + câu trả lời, ablation 3 finding.
- **Ưu tiên cắt: bảng cồng kềnh, hình trùng lặp, prose lặp ý, bib dài.**
- **Giữ narrative.** RQ1–RQ3 và câu trả lời là xương sống — không đụng logic, chỉ nén câu chữ.
- Mỗi mục dưới đây ghi **ước lượng tiết kiệm** (eRow = dòng .tex, ePage = phần trang).

---

## 1. Bảng — nguồn phình to nhất (ước cắt ~3.5–4 trang)

### 1.1 `tab:benchmark_sources` (rw_01–rw_30, 30 dòng) — **CHUYỂN SANG APPENDIX hoặc XÓA** 🔴 ưu tiên 1
- Hiện chiếm ~1.3 trang. Đây là bảng tốn diện tích nhất toàn bài.
- **Phương án A (khuyến nghị):** xóa khỏi body, thay bằng 1 câu: "Mỗi case truy về một GitHub issue/Node.js doc cụ thể; danh sách đầy đủ rw_01–rw_30 với nguồn có trong supplementary material / repo công khai."
- **Phương án B:** đẩy xuống Appendix (LNCS cho phép appendix sau refs, thường không tính page limit chính — kiểm tra CFP).
- **ePage: ~1.3 trang.**
- Giữ lại `tab:benchmark` (phân bố 10 category, 10 dòng) — đủ chứng minh benchmark real-world.

### 1.2 `tab:generators` (18 dòng generator functions) — **NÉN còn 6–7 dòng đại diện** 🔴 ưu tiên 1
- 18 dòng là quá chi tiết cho conference paper. Giữ 5–6 generator tiêu biểu (sequential_fetch, loop_parallel, callback_promise, cache, abort_controller, worker_threads), thêm dòng "... và 12 generator khác (xem repo)".
- Hoặc đổi sang prose: liệt kê inline 3–4 ví dụ thay vì bảng nguyên.
- **ePage: ~0.5 trang.**

### 1.3 Hợp nhất `tab:nopipeline` + `tab:pipeline` + `tab:ablation` → CHỈ GIỮ `tab:ablation` 🔴 ưu tiên 1
- **Ba bảng này chứa CÙNG số liệu.** `tab:ablation` (6 dòng + 3 dòng tổng) đã bao trùm hoàn toàn nopipeline và pipeline.
- Xóa `tab:nopipeline` và `tab:pipeline`, giữ nguyên `tab:ablation`.
- Prose của §4.2/§4.3 viết lại trỏ vào `tab:ablation` thay vì bảng riêng.
- **ePage: ~0.7 trang** (2 bảng + caption + vspace).

### 1.4 `tab:setup` (6 config) — **NÉN thành prose** 🟡 ưu tiên 2
- 6 dòng cấu hình có thể gói trong 1–2 câu: "Sáu cấu hình = {base, fine-tuned, GPT-3.5} × {no-pipeline, +pipeline}; scoring PASS=1.0/PARTIAL=0.5/FAIL=0."
- **ePage: ~0.3 trang.**

### 1.5 `tab:ast` (4 hàm) + `tab:patterns` (5 pattern) — **GIỮ, bảng nhỏ gọn** 🟢
- Cả hai nhỏ, mang nội dung kỹ thuật cốt lõi. Giữ. Chỉ rà prose xung quanh (xem §3).

### 1.6 `tab:taxonomy`, `tab:benchmark`, `tab:finetune` — **GIỮ** 🟢
- Đều nhỏ (4–6 dòng) và cần thiết. Giữ.

**Tổng cắt từ bảng: ~2.8–3.3 trang.**

---

## 2. Hình — xóa trùng lặp (ước cắt ~0.8–1 trang)

### 2.1 `fig:contribution` (tikz bar) VÀ `fig:ablation` (pdf bar) — **TRÙNG, giữ 1** 🔴 ưu tiên 1
- Hai hình vẽ **cùng dữ liệu** (score 6 config). Xóa `fig:contribution` (tikz inline), giữ `fig:ablation` (pdf, có hatch phân biệt pipeline rõ hơn). Hoặc ngược lại — giữ cái nào đẹp hơn khi render.
- **ePage: ~0.4 trang.**

### 2.2 `fig:category` (pdf) vs `tab:category` — **trùng thông tin** 🟡 ưu tiên 2
- Bảng per-category + hình per-category cùng số liệu. Giữ **bảng** (chính xác số), xóa **hình** — hoặc ngược lại nếu muốn visual. Khuyến nghị giữ bảng, xóa hình.
- **ePage: ~0.4 trang.**

### 2.3 `fig:overview` (pipeline tikz) — **GIỮ** 🟢
- Hình 1, reviewer hay xem đầu tiên. Giữ. Có thể thu nhỏ chiều cao nếu cần vài mm.

**Tổng cắt từ hình: ~0.8 trang.**

---

## 3. Prose dư thừa / lặp ý (ước cắt ~1.5–2 trang)

### 3.1 Câu trả lời RQ lặp lại Conclusion 🟡
- §4.2 "Answering RQ1/RQ2", §4.4 "Answering RQ3" và Conclusion + ablation enumerate **nói lại cùng ý** (retrieval chỉ giúp model có domain knowledge; nhỏ thắng GPT-3.5).
- Giữ câu trả lời RQ gọn ở Results. Conclusion **chỉ tóm 2–3 câu**, bỏ đoạn lặp lại nguyên lý "retrieval only helps..." vì đã nói ở ablation finding 1 + RQ2 answer.
- **ePage: ~0.4 trang.**

### 3.2 Background §2.1 taxonomy — prose mới thêm hơi dài 🟡
- Đoạn giải thích atomicity/order/starvation/closure sau bảng (vừa thêm) khá dài. Nén: gộp 4 mô tả category thành 2–3 câu, giữ riêng phần "closure loop var" (điểm đặc biệt JS + lý do đưa vào).
- **ePage: ~0.3 trang.**

### 3.3 §3 Proposed Approach — prose sau bảng vừa thêm 🟡
- Các đoạn giải thích `tab:generators`, `tab:ast`, `tab:finetune` mới thêm — giữ ý chính, cắt câu mở rộng (vd câu "label noise that LLM-generated synthetic data can introduce", câu về preprocessing "direct measurable effect").
- **ePage: ~0.3 trang.**

### 3.4 Dataset section — Knowledge base + benchmark prose 🟡
- Đoạn mô tả 2,050 docs và nguồn benchmark có chi tiết đếm con số (99 MDN, 50 lib, 151 pattern, 1750 synthetic...). Gộp gọn: giữ tổng 2,050 và 3 group, bỏ breakdown từng nguồn nhỏ.
- "This benchmark design eliminates the risk..." (sau tab:benchmark_sources) + "This benchmark design eliminates..." lặp ý chống bias 2 lần → giữ 1.
- **ePage: ~0.3 trang.**

### 3.5 Listing code (bug/fix closure_loop_var) — 2 listing 🟢→🟡
- Hai listing var/let mỗi cái 5 dòng. Có thể gộp thành 1 listing với comment "// bug" và "// fix", hoặc giữ (minh họa tốt). Cân nhắc nếu vẫn dư trang.
- **ePage: ~0.2 trang nếu gộp.**

### 3.6 Intro RQ block + roadmap — **GIỮ** 🟢
- User yêu cầu rõ. Không cắt. Chỉ đảm bảo roadmap 1 đoạn ngắn (đã ổn).

**Tổng cắt từ prose: ~1.5–1.8 trang.**

---

## 4. Bibliography (ước cắt ~0.5–1 trang nếu refs tính page)

### 4.1 Nén format bib 🟡
- 27 bibitem, nhiều cái là URL tool (esprima, eslint, nodejs, fastapi, kaggle, rxjs, plimit, asyncmutex, bluebird, peft, rankbm25...).
- **Không xóa citation đang dùng** (tránh \cite undefined). Nhưng:
  - Rút mô tả dài: vd "p-limit: Run Multiple Promise-Returning Functions with Limited Concurrency" → "p-limit." + URL.
  - Bỏ năm/subtitle thừa ở các software ref.
- **ePage: ~0.4 trang.**

### 4.2 Rà citation thực sự cần 🟡
- Kiểm tra cái nào chỉ \cite 1 lần ở chỗ không trọng yếu (vd kaggle, gpt35 platform url) — có thể gộp hoặc giữ. **KHÔNG xóa nếu còn \cite** trong body.
- Trước khi xóa bất kỳ bibitem nào: `grep \cite{key}` toàn file xác nhận 0 occurrence.

**Tổng cắt từ bib: ~0.5 trang.**

---

## 5. Tinh chỉnh layout (đệm, ~0.3–0.5 trang)

- Rà các `\vspace{-0.3cm}`/`-0.45cm`/`-0.5cm` quanh bảng — sau khi xóa bảng nhiều, chỉnh lại cho khít, không để khoảng trắng mồ côi.
- `\small` cho các bảng còn lại nếu cần khít cột.
- Cân nhắc `\begin{table}[t]` thay `[H]` để LaTeX float tối ưu chỗ trống (lưu ý: đổi vị trí bảng — kiểm tra lại reference text vẫn gần bảng).

---

## 6. Tổng kết ngân sách trang

| Hạng mục | Ước tiết kiệm |
|---|---|
| 1. Bảng (sources xóa, generators nén, gộp 3→1 result table, setup→prose) | ~2.8–3.3 trang |
| 2. Hình (xóa 2 hình trùng) | ~0.8 trang |
| 3. Prose lặp (RQ/conclusion, background, approach, dataset) | ~1.5–1.8 trang |
| 4. Bibliography nén | ~0.5 trang |
| 5. Layout | ~0.3 trang |
| **TỔNG** | **~5.9–6.7 trang** |

Hiện ~16 → sau cắt **~9.3–10 trang**. ❗ **Chưa đạt < 8.**

### ⇒ Cần thêm 1 trong các bước mạnh tay (chọn theo CFP):

- **Đẩy Appendix:** tab:benchmark_sources + tab:generators chi tiết + listing → appendix (nếu venue không tính appendix vào limit). Tiết kiệm thêm ~1.5 trang ⇒ **~8 trang**. ✅
- **Two-column hóa:** nếu venue cho phép `\documentclass[twocolumn]` — nén mạnh nhưng LNCS chuẩn là single-column 2-author... **kiểm tra template gốc ICCIES2026**.
- **Cắt sâu Related Work:** gộp 2 subsection (Heuristic + ML/LLM) thành 1, bỏ bớt tool ít liên quan (CodeBERT/CodeT5 chỉ giữ 1 câu). ~0.4 trang.
- **Bỏ Inference Latency section (§4.5):** nếu không phải claim chính, latency table + prose có thể đẩy 1 câu vào discussion. ~0.4 trang.

---

## 7. Thứ tự thực thi đề xuất (khi bắt đầu sửa)

1. **Xác nhận CFP:** refs có tính page? appendix có tính? single/two-column? → quyết phương án mạnh tay nào.
2. Xóa/đẩy `tab:benchmark_sources` (lớn nhất, an toàn nhất). [§1.1]
3. Gộp 3 result table → 1 `tab:ablation`, sửa prose §4.2–4.3. [§1.3]
4. Xóa 1 trong 2 ablation figure + xóa fig:category. [§2.1, §2.2]
5. Nén `tab:generators`, `tab:setup`. [§1.2, §1.4]
6. Nén prose lặp: Conclusion, Background taxonomy, dataset breakdown. [§3.1–3.4]
7. Nén bibliography format. [§4]
8. **Compile, đếm trang thực tế.** Nếu còn > 8 → áp bước mạnh tay §6 (appendix / cắt latency / cắt related work).
9. Rà lại layout, vspace, float, undefined \cite, cross-ref. [§5]
10. Compile lần cuối, xác nhận < 8 trang + không vỡ reference.

---

## 8. Checklist an toàn (không làm hỏng bài)

- [ ] Không xóa bibitem nào còn `\cite{}` trong body (grep trước khi xóa).
- [ ] Mọi bảng/hình bị xóa: gỡ luôn câu `Table~\ref{...} shows...` trỏ tới nó (tránh ref vỡ).
- [ ] Giữ nguyên: 3 RQ + 3 câu trả lời, main result 73.3%/+13.3pp/125×, ablation 3 finding.
- [ ] Giữ Figure 1 (pipeline overview).
- [ ] Sau mỗi bước compile kiểm "Rerun to get cross-references" và "undefined references".
- [ ] Backup bản hiện tại trước khi cắt (vd copy `threadlearn_paper_full.tex`).
