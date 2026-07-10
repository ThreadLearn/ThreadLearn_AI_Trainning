"""
AI2-05: JWT Authentication
Verify JWT token gửi từ Node.js backend trong header Authorization: Bearer <token>.
Dùng python-jose để decode. JWT_SECRET phải khớp với Node.js backend.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from config import JWT_SECRET

# Scheme: đọc token từ "Authorization: Bearer <token>"
# auto_error=False để tự raise 401 khi thiếu header (mặc định HTTPBearer trả 403).
_bearer = HTTPBearer(auto_error=False)

# Algorithm khớp với Node.js backend (jsonwebtoken mặc định dùng HS256)
ALGORITHM = "HS256"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """
    FastAPI dependency — verify JWT và trả về user_id.

    Dùng trong route:
        @app.post("/api/v1/ai/analyze")
        def analyze(user_id: str = Depends(get_current_user)):
            ...

    Flow:
        1. HTTPBearer tự extract token từ header
        2. jwt.decode() verify signature + expiry
        3. Lấy "sub" claim làm user_id
        4. Raise 401 nếu token sai/hết hạn

    Raises:
        HTTPException 401 — token thiếu, sai, hoặc hết hạn
        HTTPException 403 — token hợp lệ nhưng không có "sub" claim
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token thiếu claim 'sub' (user_id)",
        )

    return user_id
