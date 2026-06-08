# AI1-03: AST Parser & Preprocessor
# Owner: AI1 - An
# Status: Done
# Delivers: stripComments(), normalizeWhitespace(), extractFunctions()
# Used by: AI2-03 (race_detector), AI2-06 (rag_pipeline)

import ast
import re

def stripComments(code: str, language: str = "python") -> str:
    """Loại bỏ comments và docstrings. Hỗ trợ Python và JS."""
    if language.lower() == "python":
        try:
            # Dùng ast.unparse (Python 3.9+) sẽ tự động lọc docstring/comment chuẩn xác nhất
            parsed = ast.parse(code)
            return ast.unparse(parsed)
        except Exception:
            # Fallback nếu code bị lỗi cú pháp
            code = re.sub(r'(?m)^\s*#.*$', '', code)
            return code
    elif language.lower() in ["javascript", "js"]:
        # Xóa // comments
        code = re.sub(r'(?m)^\s*//.*$', '', code)
        # Xóa /* */ comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        return code
    return code

def normalizeWhitespace(code: str, language: str = "python") -> str:
    """Chuẩn hóa khoảng trắng và dòng trống."""
    if language.lower() == "python":
        try:
            return ast.unparse(ast.parse(code))
        except Exception:
            pass
    
    # Fallback cho JS và Python bị lỗi syntax
    # Biến nhiều dòng trống liên tiếp thành tối đa 2 dòng
    code = re.sub(r'\n{3,}', '\n\n', code)
    # Xóa khoảng trắng thừa ở cuối mỗi dòng
    code = '\n'.join([line.rstrip() for line in code.split('\n')])
    return code.strip()

def extractFunctions(code: str, language: str = "python") -> list:
    """Trích xuất danh sách các functions/classes từ file code."""
    functions = []
    if language.lower() == "python":
        try:
            parsed = ast.parse(code)
            for node in ast.walk(parsed):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        "name": node.name,
                        "type": "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function",
                        "code": ast.unparse(node)
                    })
                elif isinstance(node, ast.ClassDef):
                    functions.append({
                        "name": node.name,
                        "type": "class",
                        "code": ast.unparse(node)
                    })
        except Exception:
            pass
    elif language.lower() in ["javascript", "js"]:
        # Tạm dùng regex bắt function JS cơ bản. (Phù hợp với RAG Pipeline)
        # pattern bắt cả async/await, arrow function là rất khó bằng regex, 
        # nhưng đây là bản nhẹ để backend gọi nhanh không cần Node.js
        pattern = r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[\s\S]*?^}'
        matches = re.finditer(pattern, code, re.MULTILINE)
        for m in matches:
            functions.append({
                "name": m.group(1),
                "type": "function",
                "code": m.group(0)
            })
    return functions

def extract_keywords(code: str, language: str = "python") -> str:
    """
    Trích xuất từ khóa (tên hàm, tên biến quan trọng) từ code 
    để phục vụ hệ thống RAG tìm kiếm (loại bỏ keywords của ngôn ngữ).
    """
    keywords = []
    if language.lower() == "python":
        try:
            parsed = ast.parse(code)
            for node in ast.walk(parsed):
                if isinstance(node, ast.Name):
                    keywords.append(node.id)
                elif isinstance(node, ast.Attribute):
                    keywords.append(node.attr)
            
            import keyword
            unique_kws = set(keywords) - set(keyword.kwlist)
            return " ".join(list(unique_kws)[:20])
        except Exception:
            pass # fallback to regex
            
    # Chung cho JS / Fallback Python
    # Tìm tất cả identifier hợp lệ (chữ cái/số/dấu gạch dưới, không bắt đầu bằng số)
    tokens = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    
    stopwords = {
        'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
        'return', 'function', 'const', 'let', 'var', 'async', 'await', 'try', 'catch',
        'finally', 'throw', 'new', 'this', 'class', 'extends', 'super', 'import', 'export',
        'default', 'yield', 'true', 'false', 'null', 'undefined', 'console', 'log',
        'False', 'None', 'True', 'and', 'as', 'assert', 'def', 'del', 'elif', 'except',
        'from', 'global', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
        'raise', 'with', 'print'
    }
    
    filtered = [t for t in tokens if t not in stopwords]
    
    # Giữ lại các token độc nhất (unique) nhưng vẫn duy trì thứ tự xuất hiện ban đầu
    seen = set()
    unique_tokens = []
    for t in filtered:
        if t not in seen:
            seen.add(t)
            unique_tokens.append(t)
            
    return " ".join(unique_tokens[:20])

