"""
Session management using server-side opaque tokens.

Tokens are stored as HMAC-SHA256 hashes — never in plaintext.
Sessions use HttpOnly, Secure (prod), SameSite=Strict cookies.
No JWTs stored client-side.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.user import UserSession

_settings = get_settings()

TOKEN_BYTES = 32  # 256-bit random token


def generate_session_token() -> str:
    """Generate a cryptographically secure opaque session token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return HMAC-SHA256 hash of a session token for storage."""
    return hmac.new(
        _settings.SECRET_KEY.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """
    Create a new server-managed session.
    Returns the plaintext token to set in the cookie (stored hashed in DB).
    """
    token = generate_session_token()
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=_settings.SESSION_MAX_AGE_SECONDS
    )

    session = UserSession(
        user_id=user_id,
        session_token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    await db.flush()
    return token


async def validate_session(db: AsyncSession, token: str) -> UserSession | None:
    """
    Validate a session token. Returns the session if valid, None otherwise.
    Updates last_activity_at on success.
    """
    if not token:
        return None

    token_hash = hash_token(token)
    result = await db.execute(
        select(UserSession).where(UserSession.session_token_hash == token_hash)
    )
    session = result.scalar_one_or_none()

    if session is None or not session.is_valid:
        return None

    # Update activity timestamp
    session.last_activity_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def revoke_session(db: AsyncSession, token: str) -> bool:
    """Revoke a single session by token. Returns True if revoked."""
    token_hash = hash_token(token)
    result = await db.execute(
        select(UserSession).where(UserSession.session_token_hash == token_hash)
    )
    session = result.scalar_one_or_none()
    if session and session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        await db.flush()
        return True
    return False


async def revoke_all_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Revoke all active sessions for a user. Returns count revoked."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    )
    sessions = result.scalars().all()
    now = datetime.now(timezone.utc)
    for s in sessions:
        s.revoked_at = now
    await db.flush()
    return len(sessions)
