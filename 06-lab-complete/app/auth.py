"""
Dual Authentication: API Key + JWT

- API Key: đơn giản, dùng cho service-to-service (header X-API-Key)
- JWT: stateless, có expiry và role, dùng cho user-facing (header Authorization: Bearer)

Flow JWT:
    POST /auth/token  → trả về JWT (đổi username/password)
    Request khác      → gửi JWT trong header Authorization: Bearer <token>
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

DEMO_USERS = {
    "student": {"password": "demo123", "role": "user"},
    "teacher": {"password": "teach456", "role": "admin"},
}

_bearer = HTTPBearer(auto_error=False)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_token(username: str, role: str) -> str:
    """Tạo JWT token với expiry."""
    payload = {
        "sub": username,
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> dict:
    """Kiểm tra username/password, raise 401 nếu sai."""
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": username, "role": user["role"]}


def _decode_jwt(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired. Please login again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token.")


def verify_auth(
    bearer: HTTPAuthorizationCredentials = Security(_bearer),
    api_key: str = Security(_api_key_header),
) -> dict:
    """
    Dependency duy nhất: chấp nhận JWT hoặc API Key.
    Ưu tiên JWT nếu có. Trả về dict {username, role}.
    """
    if bearer and bearer.credentials:
        return _decode_jwt(bearer.credentials)

    if api_key:
        if api_key != settings.agent_api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return {"username": "api-key-user", "role": "user"}

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Use header 'X-API-Key: <key>' or 'Authorization: Bearer <jwt>'",
        headers={"WWW-Authenticate": "Bearer"},
    )
