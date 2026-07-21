# Hướng dẫn Kiểm thử Model sau khi vá lỗi (Dành cho Trung)
**Ngày cập nhật:** 15/06/2026

Chào Trung,

Bản model **Qwen2.5-Coder-1.5B** của chúng ta vừa được train bổ sung (continue fine-tuning) để khắc phục 5 test case bị PARTIAL (chỉ đạt 75% ở lần test trước). 
Model mới đã được đẩy đè lên repo Hugging Face: `anha12/threadlearn-qwen2.5-coder-1.5b-merged`.

Dưới đây là các bước để ông chạy lại bài test và nghiệm thu thành quả nhé.

### Bước 1: Xóa Cache Model Cũ
Thư viện `transformers` thường lưu cache model cực kỳ "lì đòn". Do mình push bản mới đè lên cùng tên cũ, ông **BẮT BUỘC** phải xóa thư mục cache của model này trên máy local để ép nó tải bản mới về.

Mở PowerShell trên máy ông và chạy:
```powershell
Remove-Item -Recurse -Force $HOME\.cache\huggingface\hub\models--anha12--threadlearn-qwen2.5-coder-1.5b-merged -ErrorAction SilentlyContinue
```
*(Nếu ông dùng Linux/Mac, chạy lệnh: `rm -rf ~/.cache/huggingface/hub/models--anha12--threadlearn-qwen2.5-coder-1.5b-merged`)*

### Bước 2: Chạy lại kịch bản Evaluation
Chạy lại script đánh giá có RAG để test trọn vẹn 20 case:
```powershell
cd f:\self_Learn\project\tool_dataset\ThreadLearn_AI_Trainning\ai2
python eval_rag_merged.py
```
*Lưu ý: Quá trình này sẽ mất chút thời gian để tải lại 3GB file `.safetensors` từ Hugging Face xuống.*

### Bước 3: Nghiệm thu 5 Test Cases (Mục tiêu 85% - 90%)
Sau khi chạy xong, ông mở file `eval_rag_results.json` và check kĩ lại 5 test case sau xem model đã sinh đúng mẫu chưa nhé:

1. **test_04 (Race Singleton Cache):** Đã cache Promise object chưa? (Sửa lỗi tạo nhiều request đồng thời).
2. **test_05 (Race File Append):** Đã chuyển sang dùng `fs.appendFile` thay vì `readFile + writeFile` chưa?
3. **test_12 (Double Callback):** Đã thêm `return cb(err)` để chặn luồng chạy tiếp chưa?
4. **test_13 (Zalgo):** Đã bọc `process.nextTick` cho callback đồng bộ chưa?
5. **test_19 (Buffer Leak):** Đã có lệnh `req.on('close', () => rs.destroy())` để dọn rác chưa?

Tui đã tạo riêng file patch JSONL và Knowledge Base đắp vào cho 5 ca này rồi, nếu nó pass từ 3-4 ca trở lên là chúng ta chính thức đạt mốc **~90% Pass Rate**. 

Check xong báo kết quả nhé! 🚀
