"""
FastAPI dependencies for authentication and authorisation.

All protected endpoints use these dependencies.
Backend enforces all permission checks — frontend checks are NOT sufficient.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User, UserSession
from app.security.session import hash_token

_settings = get_settings()


async def get_current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserSession:
    """Validate the session cookie and return the active session."""
    token = request.cookies.get(_settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    token_hash = hash_token(token)
    result = await db.execute(
        select(UserSession)
        .where(UserSession.session_token_hash == token_hash)
        .options(selectinload(UserSession.user).selectinload(User.role))
    )
    session = result.scalar_one_or_none()

    if session is None or not session.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
        )

    return session


async def get_current_user(
    session: UserSession = Depends(get_current_session),
) -> User:
    """Return the authenticated user for the current request."""
    user = session.user
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
        )
    return user


def require_permission(resource: str, action: str):
    """
    Dependency factory: enforce that the current user has a specific permission.

    Usage:
        @router.get("/patients", dependencies=[Depends(require_permission("patients", "read"))])
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not await _user_has_permission(user, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return _check


async def _user_has_permission(user: User, resource: str, action: str) -> bool:
    """Check if a user's role grants a specific resource:action permission."""
    if user.role is None:
        return False

    role = user.role
    for rp in role.permissions:
        perm = rp.permission
        if perm.resource == resource and perm.action == action:
            return True
        # Wildcard support: resource:* grants all actions on resource
        if perm.resource == resource and perm.action == "*":
            return True
        # Super wildcard: *:* grants everything (admin only)
        if perm.resource == "*" and perm.action == "*":
            return True

    return False


def require_role(role_name: str):
    """Dependency factory: enforce role membership."""
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not user.role or user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' required.",
            )
        return user

    return _check


# Pre-built common dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSession = Annotated[UserSession, Depends(get_current_session)]
