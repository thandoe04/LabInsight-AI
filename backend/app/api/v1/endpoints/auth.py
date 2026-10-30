"""
Authentication API endpoints.

Security controls:
- Argon2id password hashing
- Server-managed HttpOnly session cookies
- CSRF protection (login exempt, all other auth endpoints protected)
- Login rate limiting (5/minute per IP)
- Safe error messages (no user enumeration)
- Login event auditing
- Session revocation
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User, LoginEvent
from app.security.dependencies import CurrentUser, get_current_session
from app.security.password import verify_password, needs_rehash, hash_password
from app.security.session import create_session, revoke_session, revoke_all_user_sessions
from app.services.audit import record_audit_event

router = APIRouter()
_settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


# ─── Schemas ────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError("Password is required.")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str | None
    mfa_enabled: bool
    is_active: bool

    model_config = {"from_attributes": True}


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters.")
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v)
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character."
            )
        return v


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_auth_error() -> HTTPException:
    """Return a safe, non-enumerating authentication error."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials.",
    )


async def _log_login_event(
    db: AsyncSession,
    email: str,
    event_type: str,
    request: Request,
    user_id: Any = None,
) -> None:
    event = LoginEvent(
        user_id=user_id,
        email_attempted=email,
        event_type=event_type,
        ip_address=request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or getattr(request.client, "host", None),
        user_agent=request.headers.get("User-Agent", "")[:512],
    )
    db.add(event)
    await db.flush()


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/login", response_model=UserResponse)
@limiter.limit(f"{_settings.RATE_LIMIT_LOGIN_PER_MINUTE}/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Authenticate with email and password.

    Returns user info and sets an HttpOnly session cookie.
    Safe error messages prevent user enumeration.
    """
    # Lookup user (always do full lookup to prevent timing attacks)
    result = await db.execute(
        select(User)
        .where(User.email == body.email.lower())
        .options(selectinload(User.role).selectinload("permissions"))
    )
    user = result.scalar_one_or_none()

    # Always verify (prevents timing oracle even if user not found)
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy"
    password_ok = verify_password(body.password, user.password_hash if user else dummy_hash)

    if user is None or not password_ok:
        await _log_login_event(db, body.email, "login_failed", request)
        await db.commit()
        raise _safe_auth_error()

    if not user.is_active:
        await _log_login_event(db, body.email, "login_failed_inactive", request, user.id)
        await db.commit()
        raise _safe_auth_error()

    # Check account lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        await _log_login_event(db, body.email, "login_failed_locked", request, user.id)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked. Try again later.",
        )

    # Reset failed count on success
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    # Rehash password if params are outdated
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)

    # Create session
    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or getattr(request.client, "host", None)
    ua = request.headers.get("User-Agent", "")[:512]
    token = await create_session(db, user.id, ip_address=ip, user_agent=ua)

    await _log_login_event(db, body.email, "login_success", request, user.id)
    await record_audit_event(
        db, "login", "success",
        actor_id=user.id, actor_username=user.username,
        request=request,
    )
    await db.commit()

    # Set HttpOnly session cookie
    response.set_cookie(
        key=_settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="strict",
        max_age=_settings.SESSION_MAX_AGE_SECONDS,
        path="/",
    )

    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role.name if user.role else None,
        mfa_enabled=user.mfa_enabled,
        is_active=user.is_active,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke the current session and clear the session cookie."""
    token = request.cookies.get(_settings.SESSION_COOKIE_NAME)
    if token:
        await revoke_session(db, token)

    await record_audit_event(
        db, "logout", "success",
        actor_id=current_user.id, actor_username=current_user.username,
        request=request,
    )
    await db.commit()

    response.delete_cookie(
        key=_settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="strict",
    )


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    request: Request,
    response: Response,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke all active sessions for the current user."""
    count = await revoke_all_user_sessions(db, current_user.id)
    await record_audit_event(
        db, "logout_all", "success",
        actor_id=current_user.id, actor_username=current_user.username,
        request=request,
        metadata={"sessions_revoked": count},
    )
    await db.commit()

    response.delete_cookie(key=_settings.SESSION_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> Any:
    """Return the currently authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        role=current_user.role.name if current_user.role else None,
        mfa_enabled=current_user.mfa_enabled,
        is_active=current_user.is_active,
    )


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(f"{_settings.RATE_LIMIT_RESET_PER_MINUTE}/minute")
async def request_password_reset(
    request: Request,
    body: PasswordResetRequestSchema,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Request a password reset email.

    Always returns 204 regardless of whether the email exists.
    Never reveals whether an email address is registered.
    """
    import hashlib
    import secrets
    from datetime import timedelta
    from app.models.user import PasswordResetToken

    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(reset_token)
        await db.flush()

        # TODO: Send email with reset link (SMTP integration)
        # reset_url = f"{_settings.FRONTEND_URL}/reset-password?token={token}"
        # await send_reset_email(user.email, reset_url)

    await db.commit()
    # Always return 204 — do NOT reveal if email exists
