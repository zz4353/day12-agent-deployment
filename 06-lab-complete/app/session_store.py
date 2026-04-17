"""
Session Store — Redis-backed với fallback in-memory.

Stateless design: mọi conversation state lưu ngoài process (Redis),
để bất kỳ agent instance nào cũng đọc/ghi được.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_redis = None
_memory_store: dict = {}
USE_REDIS = False

if settings.redis_url:
    try:
        import redis as _redis_mod
        _redis = _redis_mod.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
        _redis.ping()
        USE_REDIS = True
        logger.info(f"Connected to Redis: {settings.redis_url}")
    except Exception as e:
        logger.warning(f"Redis unavailable ({e}) — using in-memory store (NOT scalable)")
        _redis = None
        USE_REDIS = False
else:
    logger.warning("REDIS_URL not set — using in-memory store (NOT scalable)")


def ping_redis() -> bool:
    """Health check: Redis có connect được không."""
    if not USE_REDIS or not _redis:
        return False
    try:
        _redis.ping()
        return True
    except Exception:
        return False


def save_session(session_id: str, data: dict, ttl_seconds: int = 3600) -> None:
    """Lưu session với TTL (mặc định 1 giờ)."""
    key = f"session:{session_id}"
    if USE_REDIS:
        _redis.setex(key, ttl_seconds, json.dumps(data))
    else:
        _memory_store[key] = data


def load_session(session_id: str) -> dict:
    """Load session, trả {} nếu không tồn tại."""
    key = f"session:{session_id}"
    if USE_REDIS:
        raw = _redis.get(key)
        return json.loads(raw) if raw else {}
    return _memory_store.get(key, {})


def delete_session(session_id: str) -> bool:
    """Xoá session, trả True nếu tồn tại trước đó."""
    key = f"session:{session_id}"
    if USE_REDIS:
        return bool(_redis.delete(key))
    return _memory_store.pop(key, None) is not None


def append_to_history(
    session_id: str,
    role: str,
    content: str,
    max_messages: int = 20,
) -> list:
    """Thêm message vào history, cắt giữ tối đa max_messages. Trả về history mới."""
    session = load_session(session_id)
    history = session.get("history", [])
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    if len(history) > max_messages:
        history = history[-max_messages:]
    session["history"] = history
    save_session(session_id, session)
    return history


def storage_info() -> dict:
    return {
        "backend": "redis" if USE_REDIS else "in-memory",
        "connected": ping_redis() if USE_REDIS else None,
    }
