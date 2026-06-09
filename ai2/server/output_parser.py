import re
from typing import List, Dict
from schemas import Issue

def clean_repetition(raw_text: str) -> str:
    """
    Loại bỏ lỗi lặp code (repetition) của model bằng cách tách các khối code
    và chỉ lấy khối hoàn chỉnh đầu tiên.
    """
    lines = raw_text.strip().split('\n')
    if not lines:
        return raw_text
        
    first_meaningful_line = None
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('//'):
            continue
            
        if first_meaningful_line is None:
            first_meaningful_line = line_stripped
        elif line_stripped == first_meaningful_line and len(line_stripped) > 5:
            # Lặp lại block logic
            return "\n".join(lines[:i]).strip()
            
    return raw_text.strip()

def cleanOutput(raw_text: str) -> Dict[str, str]:
    """
    Trích xuất `code` và `explanation` từ raw_text bằng Regex.
    Xử lý 3 trường hợp:
    1. Có 1 block ```javascript ... ```
    2. Có nhiều block (chỉ lấy block đầu tiên)
    3. Không có block nào (assume toàn bộ text là code)
    """
    # Xóa lặp code trước
    cleaned_raw = clean_repetition(raw_text)
    
    # Dùng Regex tìm block markdown code (```javascript ... ``` hoặc ```js ... ``` hoặc ``` ... ```)
    pattern = re.compile(r"```(?:javascript|js)?\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(cleaned_raw)
    
    if matches:
        # Nếu có block, lấy block đầu tiên làm code
        extracted_code = matches[0].strip()
        
        # Phần còn lại ngoài block (sau khi gỡ block đầu) sẽ là explanation
        explanation = re.sub(pattern, "", cleaned_raw, count=1).strip()
        # Loại bỏ các block thừa nếu có
        explanation = re.sub(pattern, "", explanation).strip()
        
        if not explanation:
            explanation = "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế."
            
        return {
            "code": extracted_code,
            "explanation": explanation
        }
    else:
        # Nếu không có block markdown, coi toàn bộ là code
        return {
            "code": cleaned_raw,
            "explanation": "Phát hiện mã nguồn chưa tối ưu. (No markdown block detected)"
        }

def parse_model_output(raw_output: str) -> List[Issue]:
    """
    Chuyển đổi code thô (raw_output) thành danh sách Issue cho Frontend.
    """
    parsed = cleanOutput(raw_output)
    
    issue = Issue(
        line_range="all",
        severity="high",
        description=parsed["explanation"],
        fix=f"```javascript\n{parsed['code']}\n```"
    )
    
    return [issue]
