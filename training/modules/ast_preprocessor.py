# AI1-03: AST Parser & Preprocessor
# Owner: AI1 - An
# Status: Done
# Delivers: stripComments(), normalizeWhitespace(), extractFunctions()
# Used by: AI2-03 (race_detector), AI2-06 (rag_pipeline)

import ast
import re

try:
    import esprima
    _ESPRIMA_AVAILABLE = True
except ImportError:
    _ESPRIMA_AVAILABLE = False

def _js_collect_nodes(node, node_types: tuple) -> list:
    """DFS walk qua ESTree node, thu thập nodes có type trong node_types."""
    results = []
    if not isinstance(node, (esprima.nodes.Node, dict)):
        return results
    obj = node.__dict__ if hasattr(node, '__dict__') else node
    if hasattr(node, 'type') and node.type in node_types:
        results.append(node)
    for val in obj.values() if isinstance(obj, dict) else vars(node).values():
        if isinstance(val, list):
            for item in val:
                if hasattr(item, 'type'):
                    results.extend(_js_collect_nodes(item, node_types))
        elif hasattr(val, 'type'):
            results.extend(_js_collect_nodes(val, node_types))
    return results


def _js_strip_comments_from_source(code: str) -> str:
    """Dùng esprima tolerant-parse + range để xoá comment tokens khỏi source."""
    try:
        script = esprima.parseScript(code, options={"comment": True, "tolerant": True, "range": True})
        comments = script.comments  # list of {type, value, range}
        # Xoá từ cuối về đầu để index không bị lệch
        result = list(code)
        for c in sorted(comments, key=lambda x: x.range[0], reverse=True):
            start, end = c.range
            result[start:end] = [' '] * (end - start)
        return "".join(result)
    except Exception:
        # Fallback regex nếu esprima không parse được (code bị lỗi cú pháp)
        code = re.sub(r'(?m)//.*$', '', code)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        return code


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
        if _ESPRIMA_AVAILABLE:
            return _js_strip_comments_from_source(code)
        # Fallback regex
        code = re.sub(r'(?m)^\s*//.*$', '', code)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        return code
    return code

def normalizeWhitespace(code: str, language: str = "python") -> str:
    """Chuan hoa khoang trang va dong trong."""
    if language.lower() == "python":
        try:
            return ast.unparse(ast.parse(code))
        except Exception:
            pass

    if language.lower() in ["javascript", "js"] and _ESPRIMA_AVAILABLE:
        # Parse tolerant -- neu thanh cong, unparse lai tu tokens de loai bo
        # khoang trang thua. Neu loi, dung fallback regex.
        try:
            script = esprima.parseScript(
                code, options={"tokens": True, "tolerant": True, "range": True}
            )
            tokens = script.tokens
            if tokens:
                parts = []
                prev_end = 0
                for tok in tokens:
                    start, end = tok.range
                    # Giu mot khoang trang don giua cac token
                    gap = code[prev_end:start]
                    parts.append(" " if gap.strip() == "" and prev_end > 0 else gap)
                    parts.append(tok.value)
                    prev_end = end
                return "".join(parts).strip()
        except Exception:
            pass

    # Fallback cho JS va Python loi syntax
    code = re.sub(r'\n{3,}', '\n\n', code)
    code = '\n'.join([line.rstrip() for line in code.split('\n')])
    return code.strip()


def _js_source_slice(code: str, node) -> str:
    """Lay doan source tuong ung voi node.range neu co."""
    if hasattr(node, 'range') and node.range:
        return code[node.range[0]:node.range[1]]
    return ""


def extractFunctions(code: str, language: str = "python") -> list:
    """Trich xuat danh sach cac functions/classes tu file code."""
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
        if _ESPRIMA_AVAILABLE:
            try:
                script = esprima.parseScript(
                    code, options={"tolerant": True, "range": True}
                )
                # Thu thap FunctionDeclaration, FunctionExpression, ArrowFunctionExpression
                FUNC_TYPES = (
                    "FunctionDeclaration",
                    "FunctionExpression",
                    "ArrowFunctionExpression",
                )
                for node in _js_collect_nodes(script, FUNC_TYPES):
                    # Ten ham: lay tu id neu FunctionDeclaration, else "anonymous"
                    name = "anonymous"
                    if hasattr(node, 'id') and node.id and hasattr(node.id, 'name'):
                        name = node.id.name
                    is_async = getattr(node, 'async', False)
                    func_type = "async_function" if is_async else "function"
                    if node.type == "ArrowFunctionExpression":
                        func_type = "async_arrow" if is_async else "arrow"
                    functions.append({
                        "name": name,
                        "type": func_type,
                        "code": _js_source_slice(code, node),
                    })
                return functions
            except Exception:
                pass
        # Fallback regex (chi bat function co ten, khong bat arrow)
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
            pass

    if language.lower() in ["javascript", "js"] and _ESPRIMA_AVAILABLE:
        try:
            script = esprima.parseScript(
                code, options={"tolerant": True, "tokens": True}
            )
            # Lay tat ca token kieu Identifier va String (ten API, method)
            seen = set()
            result = []
            for tok in script.tokens:
                if tok.type == "Identifier" and tok.value not in _JS_STOPWORDS:
                    if tok.value not in seen:
                        seen.add(tok.value)
                        result.append(tok.value)
            return " ".join(result[:20])
        except Exception:
            pass

    # Fallback regex cho ca JS va Python loi syntax
    tokens = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    stop = _JS_STOPWORDS | _PY_STOPWORDS
    seen: set = set()
    unique_tokens = []
    for t in tokens:
        if t not in stop and t not in seen:
            seen.add(t)
            unique_tokens.append(t)
    return " ".join(unique_tokens[:20])

