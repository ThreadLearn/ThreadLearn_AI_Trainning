"""
AI2-02: BM25 Indexing Module
Owner: AI2 - Trung
Status: Done

In-memory BM25 index over knowledge_base.json.
Built once at server startup, held in RAM.
CamelCase-aware tokenizer for JS code keyword matching.
"""

import json
import re
import time
import os
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

# Danh sách từ bị loại bỏ (stopwords) — các từ không mang nghĩa kỹ thuật.
# Ví dụ: "the", "is", "a" xuất hiện ở mọi câu → không giúp phân biệt tài liệu.
# LƯU Ý: "all" KHÔNG có trong danh sách này vì "all" có nghĩa trong JS code:
#   - Promise.all(...) → sau khi tách CamelCase còn lại "all"
#   - fetchAllUsers   → tách ra "fetch", "all", "users"
STOPWORDS = {
    "the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and",
    "or", "with", "this", "that", "it", "be", "are", "was", "were",
    "has", "have", "had", "do", "does", "did", "not", "by", "from",
    "as", "if", "when", "then", "so", "but", "also", "can", "will",
    "use", "used", "using", "should", "would", "could", "may", "each",
    "how", "what", "which", "who", "into", "after", "before",
    "its", "their", "they", "we", "you", "he", "she", "i", "me",
}


def _split_camel(token: str) -> List[str]:
    """
    Tách một chuỗi CamelCase thành các từ riêng lẻ.

    Ví dụ:
        "fetchAllUsers"     → ["fetch", "all", "users"]
        "BM25Retriever"     → ["bm25", "retriever"]
        "SharedArrayBuffer" → ["shared", "array", "buffer"]

    Cách hoạt động:
        Bước 1: re.sub(r"([a-z])([A-Z])", r"\\1 \\2", token)
            → Chèn dấu cách giữa chữ thường và chữ HOA liền sau.
            → "fetchAllUsers" → "fetch All Users"

        Bước 2: re.sub(r"([A-Z]+)([A-Z][a-z])", r"\\1 \\2", parts)
            → Xử lý chuỗi HOA liên tiếp (ví dụ: "XMLParser" → "XML Parser").
            → "XMLParser" → "XML Parser"

        Bước 3: .lower().split()
            → Chuyển hết sang chữ thường và tách bởi khoảng trắng.
    """
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", parts)
    return parts.lower().split()


def tokenize(text: str) -> List[str]:
    """
    Chuyển đổi văn bản thành danh sách token để lập chỉ mục BM25.

    Pipeline xử lý gồm 3 bước:

    Bước 1 — Tách thô theo ký tự không phải chữ/số:
        re.split(r"[^a-zA-Z0-9]+", text)
        → Xử lý: snake_case (dấu _), dấu chấm (.),
                  dấu ngoặc (), dấu phẩy, khoảng trắng, v.v.
        → "Promise.all"  → ["Promise", "all"]
        → "shared_array" → ["shared", "array"]

    Bước 2 — Tách CamelCase từng chunk (gọi _split_camel):
        → "fetchAllUsers" → ["fetch", "all", "users"]

    Bước 3 — Lọc:
        - Bỏ stopwords (từ trong STOPWORDS)
        - Bỏ token ngắn hơn 2 ký tự (ví dụ: "i", "a", "x")
        - Chuyển hết sang chữ thường

    Ví dụ đầy đủ:
        tokenize("Promise.all parallel execution")
        → ["promise", "all", "parallel", "execution"]

        tokenize("fetchAllUsers from the database")
        → ["fetch", "all", "users", "database"]
        (loại bỏ "from", "the" vì là stopwords)
    """
    # Tách văn bản thành các chunk dựa trên ký tự không phải chữ/số
    raw_tokens = re.split(r"[^a-zA-Z0-9]+", text)
    tokens = []
    for raw in raw_tokens:
        if not raw:
            continue
        # Tách thêm nếu chunk là CamelCase (ví dụ: "SharedArrayBuffer")
        for sub in _split_camel(raw):
            sub = sub.strip()
            # Chỉ giữ token có độ dài >= 2 và không nằm trong stopwords
            if len(sub) >= 2 and sub not in STOPWORDS:
                tokens.append(sub)
    return tokens


# ---------------------------------------------------------------------------
# BM25Retriever
# ---------------------------------------------------------------------------

class BM25Retriever:
    """
    Chỉ mục BM25 in-memory trên danh sách tài liệu trong knowledge base.

    BM25 (Best Match 25) là thuật toán xếp hạng tài liệu theo mức độ liên quan
    với câu truy vấn. Nó cải tiến TF-IDF bằng cách:
        - Giới hạn ảnh hưởng của tần suất từ (term frequency saturation)
        - Chuẩn hóa theo độ dài tài liệu

    Công thức điểm cho từ q trong tài liệu D:
        score(q, D) = IDF(q) × (TF(q,D) × (k1+1)) / (TF(q,D) + k1 × (1 - b + b × |D|/avgDL))
        Trong đó:
            IDF(q)  = log((N - df + 0.5) / (df + 0.5))   [N = tổng số doc, df = số doc chứa q]
            TF(q,D) = số lần từ q xuất hiện trong D
            |D|     = số token trong D
            avgDL   = độ dài trung bình của tất cả tài liệu
            k1=1.5, b=0.75 (mặc định của BM25Okapi)

    Cách dùng:
        retriever = BM25Retriever()
        retriever.build(docs)           # Gọi 1 lần lúc khởi động server
        results = retriever.search("Promise.all parallel fetch", top_k=3)
    """

    def __init__(self):
        # _index: đối tượng BM25Okapi từ thư viện rank-bm25, None trước khi build
        self._index: BM25Okapi | None = None
        # _docs: danh sách tài liệu gốc, dùng để trả về kết quả sau khi tìm kiếm
        self._docs: List[Dict[str, Any]] = []
        # _build_time_ms: thời gian build index (dùng để kiểm tra hiệu năng)
        self._build_time_ms: float = 0.0

    def build(self, docs: List[Dict[str, Any]]) -> None:
        """
        Xây dựng chỉ mục BM25 từ danh sách tài liệu.

        Mỗi tài liệu cần có ít nhất: {id, title, content, category}.
        Ghép title + content lại để lập chỉ mục → tìm kiếm toàn diện hơn.

        Ví dụ một doc trong knowledge_base.json:
            {
                "id": "js-001",
                "title": "Promise.all Pattern",
                "content": "Use Promise.all to run multiple async operations in parallel...",
                "category": "patterns"
            }

        Quá trình build:
            1. Với mỗi doc: ghép title + content → tokenize → danh sách token
            2. Tạo corpus = [[token,...], [token,...], ...] (250 danh sách)
            3. Truyền corpus vào BM25Okapi → tính IDF, lưu TF nội bộ

        Độ phức tạp: O(N × L) — N = số tài liệu, L = độ dài trung bình mỗi doc
        """
        start = time.perf_counter()

        self._docs = docs
        corpus = []
        for doc in docs:
            # Ghép title và content để tăng độ bao phủ keyword
            combined = f"{doc.get('title', '')} {doc.get('content', '')}"
            corpus.append(tokenize(combined))

        # BM25Okapi nhận vào list of token lists, tự tính IDF và thống kê corpus
        self._index = BM25Okapi(corpus)

        # Đo thời gian build (yêu cầu < 500ms cho 250 tài liệu)
        self._build_time_ms = (time.perf_counter() - start) * 1000

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Tìm kiếm top_k tài liệu liên quan nhất với câu truy vấn.

        Đầu vào thường là các keyword được AST Preprocessor trích xuất từ code
        của người dùng (ví dụ: "setTimeout race condition shared variable").

        Quy trình:
            1. Tokenize query (cùng pipeline với lúc build index)
            2. Nếu query rỗng sau tokenize → trả về []
            3. BM25 tính điểm cho từng tài liệu trong corpus
            4. Sắp xếp giảm dần theo điểm, lấy top_k
            5. Loại bỏ tài liệu có điểm = 0 (không liên quan)

        Lý do loại scores[idx] > 0:
            BM25 gán điểm 0 khi không có từ nào trong query khớp với tài liệu.
            Trả về tài liệu điểm 0 sẽ gây nhiễu cho LLM prompt.

        Ví dụ:
            search("Promise.all parallel fetch", top_k=3)
            → Trả về 3 tài liệu về Promise, parallel execution, async patterns

        Throws:
            RuntimeError — nếu gọi search() trước khi gọi build()
        """
        if self._index is None:
            raise RuntimeError("Index not built. Call build() first.")

        # Tokenize query theo cùng pipeline với corpus
        query_tokens = tokenize(query)
        if not query_tokens:
            # Query rỗng hoặc chỉ chứa stopwords → không tìm được gì
            return []

        # get_scores trả về array điểm BM25 cho từng tài liệu trong corpus
        scores = self._index.get_scores(query_tokens)

        # Lấy top_k chỉ số tài liệu có điểm cao nhất
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        # Chỉ trả về tài liệu có điểm > 0 (thực sự liên quan)
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(self._docs[idx])

        return results

    @property
    def build_time_ms(self) -> float:
        """Thời gian build index tính bằng millisecond. Dùng để kiểm tra hiệu năng."""
        return self._build_time_ms

    @property
    def doc_count(self) -> int:
        """Số lượng tài liệu đang được lập chỉ mục."""
        return len(self._docs)


# ---------------------------------------------------------------------------
# Factory: load from knowledge_base.json
# ---------------------------------------------------------------------------

def load_retriever(kb_path: str | None = None) -> BM25Retriever:
    """
    Đọc knowledge_base.json và trả về BM25Retriever đã build xong.

    Đây là hàm entry point chính — được gọi 1 lần lúc FastAPI server khởi động.
    Kết quả được giữ trong RAM suốt vòng đời server (in-memory index).

    Tham số:
        kb_path: đường dẫn tới knowledge_base.json.
                 Mặc định: ../knowledge-base/knowledge_base.json
                 (tương đối so với vị trí file này)

    Luồng xử lý:
        1. Xác định đường dẫn (mặc định hoặc từ tham số)
        2. Kiểm tra file tồn tại → raise FileNotFoundError nếu không có
        3. Đọc JSON → list 250 tài liệu
        4. Tạo BM25Retriever mới → build(docs) → trả về

    Raises:
        FileNotFoundError — nếu knowledge_base.json không tìm thấy tại đường dẫn

    Ví dụ dùng trong main.py (FastAPI):
        from bm25_module import load_retriever

        @app.on_event("startup")
        async def startup():
            app.state.retriever = load_retriever()
    """
    if kb_path is None:
        # Đường dẫn mặc định: lên 1 cấp từ server/ → knowledge-base/
        kb_path = os.path.join(
            os.path.dirname(__file__), "..", "knowledge-base", "knowledge_base.json"
        )

    # Chuẩn hóa đường dẫn (xử lý ../ và \\ trên Windows)
    kb_path = os.path.normpath(kb_path)

    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"knowledge_base.json not found at: {kb_path}")

    # Đọc toàn bộ JSON vào memory (250 docs ~ vài trăm KB, chấp nhận được)
    with open(kb_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    retriever = BM25Retriever()
    retriever.build(docs)
    return retriever
