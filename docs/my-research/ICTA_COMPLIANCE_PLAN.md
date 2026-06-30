# Kế hoạch: viết bản nghiên cứu đạt chuẩn template ICTA (Springer LNCS)

**Nguồn template:** `ICTA_Word+Template/` (icta.docm, icta Word Technical Instructions.docx, Quick Start.docx)
**Bản hiện có:** `threadlearn_paper.tex` (LaTeX `llncs.cls`, 10 trang)
**Kết luận nhanh:** ICTA = **Springer Lecture Notes in Computer Science (LNCS)**, phiên bản **Microsoft Word** (.docm có macro ribbon). Paper LaTeX hiện tại đã dùng đúng class `llncs` → **nội dung & format gốc đã đúng chuẩn LNCS**. Việc còn lại: tạo bản **đúng định dạng template yêu cầu** + rà từng yêu cầu cụ thể.

---

## 1. Template ICTA yêu cầu gì (trích từ instructions + sample icta.docm)

### 1.1 Định dạng tài liệu
| Mục | Yêu cầu ICTA/LNCS | Bản .tex hiện tại |
|---|---|---|
| Class/style | Springer LNCS proceedings | ✅ `\documentclass[runningheads]{llncs}` |
| Công cụ gốc | **Microsoft Word** (.docm) HOẶC LaTeX llncs | ⚠️ Đang LaTeX — cần xác nhận venue nhận LaTeX hay bắt buộc Word |
| Title | 14pt bold, **căn giữa** | ✅ `\title{}` |
| Authors | tên + superscript số + ORCID `[0000-...]` | ✅ có `\orcidID` |
| Affiliation | mỗi tổ chức 1 số, kèm địa chỉ + email | ✅ 3 `\inst` blocks |
| Abstract | **150–250 từ**, từ "Abstract." in đầu | ⚠️ CẦN ĐẾM (hiện ~180 từ?) |
| Keywords | "Keywords:" + danh sách, kết bằng dấu chấm | ✅ `\keywords{}` |

### 1.2 Heading (đúng 4 cấp, chỉ đánh số 2 cấp đầu)
- **1st level**: 12pt bold, đánh số `1 Introduction` ✅ `\section`
- **2nd level**: 10pt bold, đánh số `2.1 ...` ✅ `\subsection`
- **3rd level**: 10pt bold, **run-in** (không số), kết bằng dấu chấm, text theo sau cùng dòng — `\subsubsection{...}` trong llncs (kết thúc bằng `.`) ✅ ta có `\subsubsection{Static Race Detector.}`
- **4th level**: 10pt italic, run-in, không số — `\paragraph{...}` ✅
- ⚠️ **Không quá 4 cấp heading** → kiểm tra không lồng sâu hơn

### 1.3 Bảng
- **Caption ĐẶT TRÊN bảng** ✅ (booktabs, `\caption` trước `\begin{tabular}`)
- Đánh số `Table 1`, `Table 2`... ✅ auto

### 1.4 Hình
- **Caption ĐẶT DƯỚI hình** ✅
- "Fig. 1." (viết tắt Fig.) — ⚠️ llncs tự render "Fig." → OK
- **Ưu tiên vector graphics**, tránh ảnh raster cho sơ đồ ✅ (tikz vector cho Figure 1)

### 1.5 References
- Style: **square brackets [1], số liên tiếp** ✅ ta dùng `\begin{thebibliography}` → [1][2]...
- Thứ tự xuất hiện / hoặc alphabetical — LNCS chấp nhận numbered consecutive ✅
- Format mẫu LNCS: `Author, F.: Title. Journal 2(5), 99–110 (2016).` ⚠️ **CẦN RÀ** — bản .tex đang dùng style `\newblock` khác mẫu LNCS Word một chút (xem §3.4)

### 1.6 Đặt tên file
- `Smith_TitleOfMyPaper.doc` → ta nên đặt `Trung_ThreadLearn.docx` / `.pdf`

---

## 2. Khoảng cách lớn nhất: LaTeX vs Word template

**Vấn đề cốt lõi:** template ICTA phát hành ở dạng **Word .docm**. Có 2 trường hợp:

- **TH1 — Venue chấp nhận LaTeX llncs** (rất phổ biến với Springer CS proceedings): bản `.tex` hiện tại **đã gần đạt**, chỉ cần rà các điểm ⚠️ ở §1 + §3. → Ít việc, an toàn nhất. **KHUYẾN NGHỊ xác nhận điều này trước.**
- **TH2 — Venue BẮT BUỘC nộp Word .docm**: phải **port toàn bộ nội dung sang icta.docm**, dùng macro ribbon format từng phần (Title/Author/Abstract/Heading/Caption). → Nhiều việc thủ công, agent không chỉnh trực tiếp .docm có macro được; cần xuất nội dung sạch để bạn paste.

---

## 3. Việc cần làm (rà & sửa để đạt chuẩn) — áp dụng cho bản LaTeX

### 3.1 Đếm & chỉnh Abstract về 150–250 từ 🔴
- Đếm số từ abstract hiện tại. Nếu <150 → bổ sung; nếu >250 → cắt.
- Đảm bảo không có `\cite` trong abstract (LNCS khuyến nghị; ta đã bỏ rồi nhưng còn `\cite{qwen25coder}` ở câu Qwen → **kiểm tra lại, bỏ nếu có**).

### 3.2 Rà heading ≤ 4 cấp & đúng kiểu run-in 🟡
- `\section` (L1), `\subsection` (L2), `\subsubsection` (L3 run-in, kết `.`), `\paragraph` (L4 italic run-in).
- Hiện có `\paragraph{Concurrency bug taxonomy.}`, `\paragraph{BM25 retrieval.}` v.v. → đúng L4.
- Kiểm tra `\subsubsection` đều kết thúc bằng dấu chấm (yêu cầu run-in).

### 3.3 Rà caption vị trí 🟢
- Table caption trên ✅ / Figure caption dưới ✅ — đã đúng, chỉ verify.

### 3.4 Rà reference format theo mẫu LNCS Word 🟡
- Mẫu LNCS: `Author, F.: Title. In: Editor (eds.) CONF 2016, LNCS, vol. 9999, pp. 1–13. Springer, Heidelberg (2016).`
- Bản .tex dùng `J.\ Wang, ... \newblock Title. \newblock In Proc...` — **khác dấu**: LNCS Word dùng `:` sau tên, không "In Proc." mà "In: ... (eds.)".
- Quyết định: nếu nộp LaTeX, `llncs.cls` + `splncs04.bst` tự lo format → **nên chuyển bibitem thủ công sang đúng cú pháp splncs04** HOẶC giữ thbibliography nhưng sửa cho khớp mẫu (`Author, F.:` thay vì `F.\ Author.`).
- ⚠️ Đây là điểm lệch chuẩn rõ nhất hiện tại.

### 3.5 Đặt tên file đầu ra 🟢
- Xuất `Trung_ThreadLearn.pdf` (+ .tex) theo convention template.

---

## 4. Kế hoạch thực thi (sau khi bạn xác nhận TH1/TH2)

### Nếu TH1 (LaTeX được chấp nhận) — KHUYẾN NGHỊ
1. Đếm abstract, chỉnh về 150–250 từ, bỏ mọi `\cite` trong abstract.
2. Sửa toàn bộ bibitem sang đúng cú pháp LNCS (`Author, F.: Title. In: ...(eds.) CONF, LNCS vol. X, pp. Y. Springer (Year).`), hoặc chuyển sang `\bibliographystyle{splncs04}` + file `.bib`.
3. Verify heading 4 cấp, caption vị trí, Fig./Table numbering.
4. Compile, đặt tên `Trung_ThreadLearn.pdf`.
5. (Tùy chọn) Kèm 1 file `.md` checklist tự đánh giá đã đạt từng mục template.

### Nếu TH2 (bắt buộc Word)
1. Tạo bản nội dung **plain/markdown** sạch (`ThreadLearn_for_Word.md`) chứa đúng cấu trúc: Title / Authors+ORCID / Affiliation / Abstract (150-250w) / Keywords / các Section đánh số / Tables (caption trên) / Figure refs / References mẫu LNCS.
2. Bạn mở `icta.docm`, paste từng phần, bấm macro ribbon tương ứng (Title, Author, Abstract, Heading L1/L2, Caption...) để áp style.
3. Hình Figure 1 (pipeline): export tikz → PDF/EMF vector, chèn vào Word, caption dưới.
4. Lưu `Trung_ThreadLearn.docx`.
- Agent KHÔNG chỉnh trực tiếp .docm (macro/binary) — chỉ cung cấp nội dung đã cấu trúc + hướng dẫn paste.

---

## 5. Checklist tuân thủ ICTA (đánh dấu khi xong)

- [ ] Abstract 150–250 từ, không citation
- [ ] Keywords có, kết bằng dấu chấm
- [ ] Title 14pt bold center / Authors + ORCID `[....]` / Affiliation + email
- [ ] Heading ≤ 4 cấp; L1/L2 đánh số, L3 bold run-in, L4 italic run-in
- [ ] Table caption TRÊN; Figure caption DƯỚI
- [ ] Vector graphics cho sơ đồ (Figure 1 tikz/PDF)
- [ ] References [n] consecutive, đúng mẫu LNCS (`Author, F.: Title...`)
- [ ] Tên file `Trung_ThreadLearn.*`
- [ ] (Word) đã dùng macro ribbon style cho từng phần
- [ ] Không vượt giới hạn trang của venue (xác nhận CFP)

---

## 6. RÀNG BUỘC ĐÃ XÁC NHẬN (ICTA2026 Submission Guidelines)
- ⛔ **BẮT BUỘC Springer Word template (.docm)** → đi theo **TH2**.
- ⛔ **≤ 8 trang** (khuyến nghị); **tối đa 10 trang**, mỗi trang dư >8 phụ thu **$10**. → **nhắm đúng 8 trang** để khỏi phí.
- English; nộp qua **EasyChair**; deadline **30/6/2026**; chọn 1 primary + 1 secondary topic.
- Final paper trong 7 ngày sau accept; tuân Springer Copyright & Permissions (third-party content).

## 7. Sản phẩm bàn giao (vì agent KHÔNG sửa .docm binary/macro được)
1. **`ThreadLearn_ICTA_WordReady.md`** — toàn bộ nội dung đã cấu trúc đúng LNCS, mỗi block ghi rõ **style macro cần bấm** trong icta.docm (Title / Author / ORCID / Affiliation / Abstract / Keywords / Heading L1-L4 / Caption). Nội dung đã nén nhắm 8 trang.
2. Bạn mở `icta.docm`, paste từng block, bấm nút ribbon tương ứng.
3. Figure 1 (pipeline): export tikz → PDF/EMF vector, chèn, caption dưới (bấm macro "Figure caption").
4. References: viết sẵn đúng mẫu LNCS `Author, F.: Title. In: Editor (eds.) CONF, LNCS vol. X, pp. Y–Z. Springer (Year).`
5. Lưu `Trung_ThreadLearn.docx`.

## 8. Điều chỉnh để khít 8 trang trong Word
- Word LNCS render đặc hơn LaTeX đôi chút; bản .tex 10 trang ≈ 8–9 trang Word, nhưng **cần cắt thêm ~1 mục an toàn**.
- Ưu tiên (đã thống nhất giữ narrative): giữ Figure 1, ablation table, 3 RQ. Nếu vượt 8: rút Future Work còn 1 câu, gộp Background vào Intro, hoặc bỏ benchmark distribution table (giữ 1 câu).
