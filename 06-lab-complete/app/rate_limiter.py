"""
In-Memory Sliding Window Rate Limiter.

Trong production multi-instance: thay bằng Redis-based (xem settings.redis_url).
"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException

from app.config import settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._windows: dict[str, deque] = defaultdict(deque)

    def check(self, user_id: str) -> dict:
        """Raise 429 nếu vượt. Trả về thông tin quota còn lại."""
        now = time.time()
        window = self._windows[user_id]

        while window and window[0] < now - self.window_seconds:
            window.popleft()

        reset_at = int(now) + self.window_seconds

        if len(window) >= self.max_requests:
            oldest = window[0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.max_requests,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                    "Retry-After": str(retry_after),
                },
            )

        window.append(now)
        return {
            "limit": self.max_requests,
            "remaining": self.max_requests - len(window),
            "reset_at": reset_at,
        }


rate_limiter_user = RateLimiter(max_requests=settings.rate_limit_per_minute)
rate_limiter_admin = RateLimiter(max_requests=settings.rate_limit_per_minute * 5)


def get_limiter(role: str) -> RateLimiter:
    return rate_limiter_admin if role == "admin" else rate_limiter_user
