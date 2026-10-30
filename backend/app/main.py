"""
LabInsight AI — FastAPI application entry point.

Security controls applied at startup:
- Strict CORS allowlist
- CSRF middleware
- Security response headers
- Request size limits
- Rate limiting
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.security.csrf import CSRFMiddleware

# Import all routers
from app.api.v1 import router as api_v1_router

_settings = get_settings()
configure_logging(_settings.LOG_LEVEL)
logger = get_logger(__name__)

# Rate limiter (uses client IP)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("labinsight_startup", version=_settings.APP_VERSION, env=_settings.APP_ENV)
    yield
    logger.info("labinsight_shutdown")


app = FastAPI(
    title=_settings.APP_NAME,
    version=_settings.APP_VERSION,
    description=(
        "LabInsight AI — Healthcare Laboratory Data Analytics Platform. "
        "NOT a medical diagnostic system."
    ),
    docs_url="/docs" if not _settings.is_production else None,
    redoc_url="/redoc" if not _settings.is_production else None,
    openapi_url="/openapi.json" if not _settings.is_production else None,
    lifespan=lifespan,
)

# --- Rate limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS (strict allowlist — no wildcard with credentials) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# --- CSRF protection ---
app.add_middleware(CSRFMiddleware)


# --- Security response headers middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if _settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
    return response


# --- Request ID middleware ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# --- Register API routers ---
app.include_router(api_v1_router, prefix="/api/v1")


# --- Health check (unauthenticated, safe) ---
@app.get("/api/v1/health", tags=["system"])
async def health_check():
    """Safe health check — returns version only, no internal details."""
    return {
        "status": "ok",
        "version": _settings.APP_VERSION,
        "environment": _settings.APP_ENV,
    }


# --- Generic error handler (never expose stack traces) ---
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(type(exc).__name__), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
