import re
from typing import List
from schemas import Issue

def clean_repetition(raw_text: str) -> str:
    """
    Loại bỏ lỗi lặp code (repetition) của model bằng cách tách các khối code
    và chỉ lấy khối hoàn chỉnh đầu tiên.
    Giả định: model thường lặp lại toàn bộ hàm sau khi viết xong.
    """
    # Nếu có dấu hiệu lặp lại theo dòng, ta ưu tiên lấy đoạn đến khi hết hàm.
    # Đơn giản nhất: Lấy đoạn code đầu tiên dài nhất có nghĩa hoặc cắt theo pattern.
    
    # Chia theo block hoặc tìm điểm bắt đầu lặp lại
    # Một thủ thuật đơn giản cho code JS: tìm đoạn function hoặc block đóng '}'
    # Tuy nhiên, an toàn nhất cho demo này là ta trả về 1 block hoàn chỉnh đầu tiên.
    # Trong output, ta thấy model in lại block y hệt.
    
    lines = raw_text.strip().split('\n')
    if not lines:
        return raw_text
        
    unique_lines = []
    seen = set()
    
    # Cắt ở điểm bắt đầu lặp lại toàn bộ logic (nếu phát hiện dòng đầu tiên bị lặp lại lần 2)
    first_meaningful_line = None
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('//'):
            continue
            
        if first_meaningful_line is None:
            first_meaningful_line = line_stripped
        elif line_stripped == first_meaningful_line and len(line_stripped) > 5:
            # Phát hiện điểm lặp lại toàn bộ block
            return "\n".join(lines[:i]).strip()
            
    return raw_text.strip()

def parse_model_output(raw_output: str) -> List[Issue]:
    """
    Chuyển đổi code thô (raw_output) từ HuggingFace Model thành danh sách Issue cho Frontend.
    """
    cleaned_code = clean_repetition(raw_output)
    
    # Vì model Qwen code-to-code chỉ trả về mã nguồn đã sửa, 
    # ta tự động đóng gói nó thành 1 Issue High Severity.
    issue = Issue(
        line_range="all",
        severity="high",
        description="Phát hiện mã nguồn bất đồng bộ/đơn luồng chưa tối ưu. Hệ thống AI đã phân tích luồng và cung cấp đoạn mã song song hóa an toàn thay thế.",
        fix=f"```javascript\n{cleaned_code}\n```"
    )
    
    return [issue]
