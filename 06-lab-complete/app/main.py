"""
Production AI Agent — kết hợp tất cả Day 12 concepts.

Checklist:
  - Config từ environment (12-factor)
  - Structured JSON logging
  - Dual auth (API Key + JWT)
  - Role-based rate limiting
  - Cost guard (per-user + global budget)
  - Input validation (Pydantic)
  - Multi-turn chat với Redis session (stateless)
  - Health + Readiness probe (kiểm tra Redis, memory)
  - Graceful shutdown với in-flight request tracking
  - Security headers + CORS
"""
import os
import time
import signal
import uuid
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_auth, authenticate_user, create_token
from app.rate_limiter import get_limiter
from app.cost_guard import cost_guard
from app import session_store
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
INSTANCE_ID = os.getenv("INSTANCE_ID") or f"instance-{uuid.uuid4().hex[:6]}"
_is_ready = False
_request_count = 0
_error_count = 0
_in_flight_requests = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "instance_id": INSTANCE_ID,
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "storage": session_store.storage_info(),
    }))
    time.sleep(0.1)
    _is_ready = True
    logger.info(json.dumps({"event": "ready", "instance_id": INSTANCE_ID}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown_start", "instance_id": INSTANCE_ID}))

    # Chờ các request đang xử lý hoàn thành (max 30s)
    timeout = 30
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:
        logger.info(json.dumps({
            "event": "waiting_in_flight",
            "in_flight": _in_flight_requests,
            "elapsed": elapsed,
        }))
        time.sleep(1)
        elapsed += 1

    logger.info(json.dumps({"event": "shutdown_complete", "instance_id": INSTANCE_ID}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count, _in_flight_requests
    start = time.time()
    _request_count += 1
    _in_flight_requests += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Instance-Id"] = INSTANCE_ID
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
            "instance_id": INSTANCE_ID,
        }))
        return response
    except Exception:
        _error_count += 1
        raise
    finally:
        _in_flight_requests -= 1


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str
    usage: dict


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": INSTANCE_ID,
        "endpoints": {
            "login": "POST /auth/token",
            "ask": "POST /ask (single-turn)",
            "chat": "POST /chat (multi-turn with session)",
            "history": "GET /chat/{session_id}/history",
            "my_usage": "GET /me/usage",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/auth/token", tags=["Auth"])
def login(body: LoginRequest):
    """Đổi username/password lấy JWT token (expires 60 phút)."""
    user = authenticate_user(body.username, body.password)
    token = create_token(user["username"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": 60,
    }


def _enforce_quotas(user: dict) -> dict:
    rate_info = get_limiter(user["role"]).check(user["username"])
    cost_guard.check_budget(user["username"])
    return rate_info


def _record_llm_cost(username: str, question: str, answer: str):
    input_tokens = len(question.split()) * 2
    output_tokens = len(answer.split()) * 2
    return cost_guard.record_usage(username, input_tokens, output_tokens)


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    user: dict = Depends(verify_auth),
):
    """Single-turn. Không lưu history."""
    rate_info = _enforce_quotas(user)

    logger.info(json.dumps({
        "event": "agent_call",
        "endpoint": "ask",
        "user": user["username"],
        "q_len": len(body.question),
    }))

    answer = llm_ask(body.question)
    usage = _record_llm_cost(user["username"], body.question, answer)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        usage={
            "requests_remaining": rate_info["remaining"],
            "cost_usd": usage.total_cost_usd,
            "budget_remaining_usd": max(0, settings.daily_budget_usd - usage.total_cost_usd),
        },
    )


@app.post("/chat", tags=["Agent"])
async def chat(
    body: ChatRequest,
    user: dict = Depends(verify_auth),
):
    """
    Multi-turn chat. State lưu trong Redis (stateless design).
    Gửi session_id ở các request sau để tiếp tục cuộc trò chuyện.
    """
    rate_info = _enforce_quotas(user)

    session_id = body.session_id or str(uuid.uuid4())

    # Ghi câu hỏi vào history
    session_store.append_to_history(session_id, "user", body.question)
    history = session_store.load_session(session_id).get("history", [])

    # Gọi LLM (mock chỉ dùng câu hỏi hiện tại; prod có thể feed cả history)
    answer = llm_ask(body.question)

    session_store.append_to_history(session_id, "assistant", answer)

    usage = _record_llm_cost(user["username"], body.question, answer)

    return {
        "session_id": session_id,
        "question": body.question,
        "answer": answer,
        "turn": len([m for m in history if m["role"] == "user"]),
        "served_by": INSTANCE_ID,
        "storage": session_store.storage_info()["backend"],
        "usage": {
            "requests_remaining": rate_info["remaining"],
            "cost_usd": usage.total_cost_usd,
        },
    }


@app.get("/chat/{session_id}/history", tags=["Agent"])
def get_history(session_id: str, user: dict = Depends(verify_auth)):
    """Xem conversation history của một session."""
    session = session_store.load_session(session_id)
    if not session:
        raise HTTPException(404, f"Session {session_id} not found or expired")
    messages = session.get("history", [])
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


@app.delete("/chat/{session_id}", tags=["Agent"])
def delete_session(session_id: str, user: dict = Depends(verify_auth)):
    """Xoá session (user logout)."""
    deleted = session_store.delete_session(session_id)
    return {"deleted": deleted, "session_id": session_id}


@app.get("/me/usage", tags=["Agent"])
def my_usage(user: dict = Depends(verify_auth)):
    """Xem usage của bản thân hôm nay."""
    return cost_guard.get_usage(user["username"])


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe. Kiểm tra memory, Redis connection."""
    checks = {"llm": "mock" if not settings.openai_api_key else "openai"}

    # Memory check
    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["memory"] = {
            "status": "ok" if mem.percent < 90 else "degraded",
            "used_percent": mem.percent,
        }
    except ImportError:
        checks["memory"] = {"status": "ok", "note": "psutil not installed"}

    # Redis check (optional — degraded chứ không fail)
    storage = session_store.storage_info()
    checks["storage"] = storage

    overall = "ok"
    if checks.get("memory", {}).get("status") == "degraded":
        overall = "degraded"
    if storage["backend"] == "redis" and not storage["connected"]:
        overall = "degraded"

    return {
        "status": overall,
        "instance_id": INSTANCE_ID,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "in_flight": _in_flight_requests,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe. Load balancer ngắt traffic nếu fail."""
    if not _is_ready:
        raise HTTPException(503, "Not ready")

    storage = session_store.storage_info()
    if storage["backend"] == "redis" and not storage["connected"]:
        raise HTTPException(503, "Redis not available")

    return {"ready": True, "instance_id": INSTANCE_ID, "in_flight": _in_flight_requests}


@app.get("/metrics", tags=["Operations"])
def metrics(user: dict = Depends(verify_auth)):
    """Basic metrics (protected). Admin có thêm global view."""
    base = {
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "in_flight_requests": _in_flight_requests,
        "error_count": _error_count,
    }
    if user["role"] == "admin":
        base["global_cost_usd"] = round(cost_guard._global_cost, 4)
        base["global_budget_usd"] = cost_guard.global_daily_budget_usd
    return base


def _handle_signal(signum, _frame):
    logger.info(json.dumps({
        "event": "signal",
        "signum": signum,
        "instance_id": INSTANCE_ID,
    }))


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} ({INSTANCE_ID}) on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
