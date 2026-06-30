# Kế hoạch Migrate Model v2 (CoT) vào Pipeline Production

Bối cảnh đầy đủ: xem [`RESEARCH_LOG.md`](RESEARCH_LOG.md). Tóm tắt vấn đề: model v2 đứng một mình tốt hơn hẳn v1 (76.7% vs 63.3%), nhưng kết quả "v2 + pipeline" hiện có (63.3%) dùng một prompt format thử nghiệm trong notebook — **khác với** format production thật trong `ai2/server/rag_pipeline.py`. Trước khi kết luận pipeline không hợp với v2, phải test lại bằng đúng code production.

---

## Nguyên tắc xuyên suốt

Bài học từ lỗi #4 (README mục 8): **fine-tune và inference phải dùng cùng một format prompt.** Mọi bước dưới đây ưu tiên giữ format nhất quán giữa (a) lúc Ân train v2, (b) lúc eval, (c) lúc chạy production — thay vì để 3 nơi tự chế 3 format khác nhau như hiện tại.

---

## Bước 0 — Thu thập thông tin còn thiếu (làm trước, không cần code)

Cần hỏi Ân trực tiếp, vì đây là thông tin không nằm trong repo:

- [ ] **Format prompt lúc train v2 chính xác là gì?** Notebook eval không-pipeline dùng `"Convert to concurrent JavaScript:\n\n{code}\n"` (giống v1) và ra 76.7% — nhưng cần Ân xác nhận đây đúng là format dùng lúc fine-tune, không phải trùng hợp.
- [ ] **v2 có học cách dùng reference context khi train không?** Nếu dataset training của v2 hoàn toàn không có ví dụ nào kèm context tài liệu tham khảo, thì *bất kỳ* cách nhét context nào lúc inference đều là out-of-distribution — không riêng gì format "Reference {i}" trong notebook.
- [ ] **HuggingFace repo / Kaggle dataset path của v2** để tải về `models/merged_v2/`.

→ Nếu câu trả lời cho mục 2 là "không, dataset không có context" — đây đổi hẳn hướng giải quyết (xem Phương án B ở Bước 3).

## Bước 1 — Đưa model v2 vào repo (hạ tầng)

```bash
cd ThreadLearn-AI-Trainning
huggingface-cli download anha12/threadlearn-qwen2.5-coder-1.5b-cot-v2 \
  --local-dir models/merged_v2
```

- [ ] Verify `config.json` model_type khớp `qwen2` (giống base/merged hiện có).
- [ ] Thêm `models/merged_v2/` vào `docs/STRUCTURE.md`.
- [ ] **Không xóa `models/merged/` (v1)** — cần giữ làm baseline so sánh, và làm fallback nếu v2 không ổn định hơn sau khi sửa pipeline.

## Bước 2 — Test v2 qua `rag_pipeline.py` thật (không phải notebook tự chế)

Đây là bước quan trọng nhất — trả lời câu hỏi "pipeline production thật sự có hại v2 không, hay chỉ notebook bị sai format".

- [ ] Sửa `ai2/server/config.py` / `.env`: thêm biến trỏ `MODEL_PATH` có thể chọn `models/merged` hoặc `models/merged_v2` (hiện tại model path có thể đang hardcode — cần kiểm tra `llm_client.py`).
- [ ] Viết script eval mới `ai2/eval/scripts/eval_v2_with_real_pipeline.py`, **bắt buộc tái sử dụng `_build_prompt()` từ `rag_pipeline.py`** (import trực tiếp, không copy-paste lại như notebook đã làm) — tránh lặp lại lỗi 3-format-khác-nhau.
- [ ] Chạy lại đúng 30-case real-world benchmark (`ai2/tests/real_world/cases/real_world_test_cases.json`) với v2 + `_build_prompt()` thật.
- [ ] So sánh 3 hàng: v2 (no pipeline, 76.7% — baseline đã có) / v2 + `_build_prompt()` thật / v2 + notebook format (63.3% — đã có, để đối chiếu).

**Kỳ vọng:** nếu v2 + `_build_prompt()` thật vẫn tệ tương đương 63.3%, vấn đề không phải do format "Reference" sai mà do model v2 **chưa từng thấy context lúc train** (xem Bước 0, mục 2) → chuyển Phương án B.

## Bước 3 — Phương án xử lý theo kết quả Bước 2

### Phương án A — Format đúng cứu được pipeline

Nếu dùng `_build_prompt()` thật đưa v2+pipeline về gần mức v1+pipeline (73.3%) hoặc cao hơn:

- [ ] Chốt `_build_prompt()` hiện tại làm chuẩn duy nhất — xóa hàm `build_prompt()` trùng lặp trong các notebook (`kaggle_pipeline_merged_v2.ipynb` và tương tự), thay bằng import từ `rag_pipeline.py` hoặc copy nguyên văn có ghi rõ "sync với rag_pipeline.py ngày X".
- [ ] Swap `MODEL_PATH` production sang `models/merged_v2`.
- [ ] Re-run toàn bộ benchmark 30-case + 20-case để có baseline mới đầy đủ, cập nhật `ai2/tests/real_world/README.md`.

### Phương án B — v2 chưa học cách dùng context (nhiều khả năng hơn dựa trên evidence hiện tại)

Nếu v2 không hề học context lúc train (dataset CoT chỉ có code→code, không có context→code), thì cách inject RAG hiện tại — bất kể format nào — đều đẩy model vào tình huống chưa từng gặp. Hai hướng:

**B1 — Train lại v2 với context trong dữ liệu (tốn nhất, lợi nhất):**
- [ ] Ân bổ sung dataset: mỗi mẫu training thêm 1-3 đoạn context giả lập (lấy từ `knowledge_base.json`, retrieve bằng chính BM25 hiện tại để mô phỏng đúng input lúc production) → format giống hệt `_build_prompt()`.
- [ ] Fine-tune v3 trên dataset mới này.
- [ ] Đây chính là cách v1 "vô tình" hoạt động tốt: dù training set không có context, nhưng model 1.5B base đã quen nhiều dạng input khác nhau qua pretraining; CoT fine-tune có thể đã "ghi đè" khả năng đó mạnh hơn.

**B2 — Dùng v2 không pipeline, bỏ RAG cho route này (rẻ, nhanh, có thể đủ tốt):**
- [ ] Vì v2 không pipeline (76.7%) đã vượt v1+pipeline (73.3%), có thể **không cần RAG cho v2** — set route production: nếu `MODEL_VERSION == "cot-v2"` thì bỏ qua BM25 retrieval, gọi thẳng model.
- [ ] Lợi: đơn giản hóa, giảm latency (không cần BM25 search + context dài hơn → tokens ít hơn → nhanh hơn).
- [ ] Rủi ro: chưa biết liệu RAG có giúp các category mà v2 còn yếu (Race Condition 50%, Zalgo 50%, Stream Leak 50% — xem RESEARCH_LOG) nếu dùng đúng cách. Đánh đổi giữa "chắc ăn 76.7%" và "có thể cao hơn nhưng chưa chứng minh được".

**Khuyến nghị thực hiện B2 trước (1-2 ngày), B1 sau nếu cần đẩy điểm cao hơn nữa** — B2 không cần train lại, validate được ngay, và đã có baseline đủ tốt để dùng cho báo cáo trong lúc chờ B1.

## Bước 4 — Cập nhật báo cáo / docx (sau khi chốt phương án)

- [ ] `docs/my-research/Trung_ThreadLearn_v2.docx` hiện dùng số liệu v1 (73.3%). Nếu B2 thắng, đổi toàn bộ Section 5 sang số liệu v2 (76.7%), note rõ "phiên bản CoT, không dùng RAG retrieval".
- [ ] Cập nhật Discussion (Section 6) — implication mới: "model nhỏ + CoT fine-tune có thể không cần RAG nếu domain knowledge đã đủ trong adapter weights" — đối lập với finding cũ "RAG chỉ giúp model đã có domain knowledge". Đây là 1 finding thú vị, đáng nêu rõ trong limitation/discussion thay vì giấu đi.
- [ ] README.md Section 7 (kết quả) — thêm hàng "ThreadLearn CoT v2" vào bảng so sánh.

## Bước 5 — Dọn dẹp kỹ thuật

- [ ] Quyết định giữ hay xóa `models/merged` (v1) sau khi v2 production-ready — khuyến nghị **giữ** ít nhất đến hết kỳ báo cáo, làm baseline reproducibility.
- [ ] Đồng bộ 1 nguồn duy nhất cho `build_prompt`/`_build_prompt` — hiện có 2 bản trùng logic (`rag_pipeline.py` và mọi notebook copy tay). Tệ nhất là sửa 1 chỗ quên sửa chỗ kia (đúng như đã xảy ra). Cân nhắc: notebook Kaggle import trực tiếp file `.py` qua upload, hoặc ít nhất ghi comment "// SYNC WITH rag_pipeline.py — copy nguyên văn".

---

## Checklist tóm tắt theo thứ tự ưu tiên

1. Hỏi Ân: prompt format train v2 + có context trong training data không (Bước 0)
2. Tải v2 vào `models/merged_v2/` (Bước 1)
3. Eval v2 + `_build_prompt()` thật, đối chiếu với 63.3% hiện có (Bước 2)
4. Theo kết quả: chốt Phương án A hoặc B2 trước, B1 sau nếu còn thời gian (Bước 3)
5. Cập nhật báo cáo + dọn code trùng lặp (Bước 4-5)
