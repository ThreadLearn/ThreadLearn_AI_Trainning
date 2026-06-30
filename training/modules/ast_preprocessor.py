# AI1-03: AST Parser & Preprocessor
# Owner: AI1 - An
# Status: Done
# Delivers: stripComments(), normalizeWhitespace(), extractFunctions()
# Used by: AI2-03 (race_detector), AI2-06 (rag_pipeline)

import ast
import re
import subprocess
import json
import os

def call_js_ast_helper(code: str, action: str):
    """Gọi Node.js subprocess để xử lý AST thực thụ cho JavaScript (Babel)."""
    helper_path = os.path.join(os.path.dirname(__file__), "js_ast_helper.js")
    try:
        process = subprocess.Popen(
            ["node", helper_path, action],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        stdout, stderr = process.communicate(input=code)
        res = json.loads(stdout)
        if "error" in res:
            return None # Fallback nếu lỗi syntax
        return res["result"]
    except Exception as e:
        return None

def stripComments(code: str, language: str = "python") -> str:
    """Loại bỏ comments và docstrings. Hỗ trợ Python và JS."""
    if language.lower() == "python":
        try:
            parsed = ast.parse(code)
            return ast.unparse(parsed)
        except Exception:
            code = re.sub(r'(?m)^\s*#.*$', '', code)
            return code
    elif language.lower() in ["javascript", "js"]:
        # Gọi AST thật bằng Babel qua Node.js Subprocess
        js_result = call_js_ast_helper(code, "strip_comments")
        if js_result is not None:
            return js_result
            
        # Fallback nếu lỗi Syntax
        code = re.sub(r'(?m)^\s*//.*$', '', code)
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
    elif language.lower() in ["javascript", "js"]:
        js_result = call_js_ast_helper(code, "normalize_whitespace")
        if js_result is not None:
            return js_result
            
    # Fallback cho JS lỗi syntax và Python lỗi syntax
    code = re.sub(r'\n{3,}', '\n\n', code)
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
        # Gọi AST thật (Babel) thay vì Regex mạo danh
        js_functions = call_js_ast_helper(code, "extract_functions")
        if js_functions is not None:
            return js_functions
            
        # Fallback regex nếu file lỗi cú pháp nặng
        pattern = r'(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{[\s\S]*?^}'
        for m in re.finditer(pattern, code, re.MULTILINE):
            functions.append({"name": m.group(1), "type": "function", "code": m.group(0)})

    return functions

_JS_STOPWORDS = {
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
    'return', 'function', 'const', 'let', 'var', 'async', 'await', 'try', 'catch',
    'finally', 'throw', 'new', 'this', 'class', 'extends', 'super', 'import', 'export',
    'default', 'yield', 'true', 'false', 'null', 'undefined', 'console', 'log',
    'of', 'in', 'typeof', 'instanceof', 'void', 'delete', 'debugger',
}

_PY_STOPWORDS = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'def', 'del', 'elif', 'except',
    'from', 'global', 'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass',
    'raise', 'with', 'print', 'if', 'else', 'for', 'while', 'return', 'class',
    'import', 'try', 'finally', 'yield',
}

def extract_keywords(code: str, language: str = "python") -> str:
    """Extract identifier keywords from code for RAG query."""
    if language.lower() == "python":
        try:
            parsed = ast.parse(code)
            keywords = []
            for node in ast.walk(parsed):
                if isinstance(node, ast.Name):
                    keywords.append(node.id)
                elif isinstance(node, ast.Attribute):
                    keywords.append(node.attr)
            import keyword as _kw
            stop = _PY_STOPWORDS | set(_kw.kwlist)
            unique = list(dict.fromkeys(k for k in keywords if k not in stop))
            return " ".join(unique[:20])
        except Exception:
            pass # fallback to regex
            
    # Xử lý JS bằng Babel
    if language.lower() in ["javascript", "js"]:
        js_kws = call_js_ast_helper(code, "extract_keywords")
        if js_kws is not None:
            return js_kws
            
    # Fallback bằng Regex
    tokens = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    stop = _JS_STOPWORDS | _PY_STOPWORDS
    seen = set()
    unique_tokens = []
    for t in tokens:
        if t not in stop and t not in seen:
            seen.add(t)
            unique_tokens.append(t)
    return " ".join(unique_tokens[:20])
