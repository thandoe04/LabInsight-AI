"""
CSRF protection middleware.

For all state-changing requests (POST, PUT, PATCH, DELETE),
verify that the X-CSRF-Token header matches the value in the session cookie.
"""
from __future__ import annotations

import secrets
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_settings = get_settings()

CSRF_COOKIE_NAME = "labinsight_csrf"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Endpoints exempt from CSRF (e.g. initial login uses credentials)
CSRF_EXEMPT_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
})


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Issue CSRF token on safe requests if not present
        response = await self._handle(request, call_next)
        return response

    async def _handle(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if request.method not in SAFE_METHODS and path not in CSRF_EXEMPT_PATHS:
            # Verify CSRF token
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(_settings.CSRF_TOKEN_HEADER)

            if not cookie_token or not header_token:
                from fastapi.responses import JSONResponse
                logger.warning("csrf_missing_token", path=path, method=request.method)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing."},
                )

            if not secrets.compare_digest(cookie_token, header_token):
                from fastapi.responses import JSONResponse
                logger.warning("csrf_token_mismatch", path=path, method=request.method)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token invalid."},
                )

        response = await call_next(request)

        # Issue or refresh CSRF token on safe requests
        if request.method in SAFE_METHODS:
            existing = request.cookies.get(CSRF_COOKIE_NAME)
            if not existing:
                csrf_token = secrets.token_urlsafe(32)
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=csrf_token,
                    httponly=False,   # Must be readable by JS to set in header
                    secure=_settings.cookie_secure,
                    samesite="strict",
                    max_age=_settings.SESSION_MAX_AGE_SECONDS,
                )

        return response
