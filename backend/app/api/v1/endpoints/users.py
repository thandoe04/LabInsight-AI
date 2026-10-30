"""
User and Role administration API endpoints.
Enforces RBAC and prevents privilege escalation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import Role, User
from app.security.dependencies import CurrentUser, require_role
from app.security.password import hash_password
from app.services.audit import record_audit_event

router = APIRouter()


class RoleResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str | None


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    full_name: str = Field(..., min_length=2, max_length=256)
    password: str = Field(..., min_length=12)
    role_id: uuid.UUID


class UserUpdate(BaseModel):
    full_name: str | None = None
    role_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserDetailResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role_name: str | None
    role_display: str | None
    is_active: bool
    mfa_enabled: bool
    created_at: datetime


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List available system roles."""
    res = await db.execute(select(Role).order_by(Role.name))
    roles = res.scalars().all()
    return [
        RoleResponse(
            id=str(r.id),
            name=r.name,
            display_name=r.display_name,
            description=r.description,
        )
        for r in roles
    ]


@router.get("", response_model=list[UserDetailResponse])
async def list_users(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List registered users and assigned roles."""
    res = await db.execute(select(User).options(selectinload(User.role)).order_by(User.created_at.desc()))
    users = res.scalars().all()
    return [
        UserDetailResponse(
            id=str(u.id),
            email=u.email,
            username=u.username,
            full_name=u.full_name,
            role_name=u.role.name if u.role else None,
            role_display=u.role.display_name if u.role else None,
            is_active=u.is_active,
            mfa_enabled=u.mfa_enabled,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    body: UserCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new user account with an assigned role."""
    # Check duplicate email or username
    existing = await db.execute(select(User).where((User.email == body.email.lower()) | (User.username == body.username)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User with this email or username already exists.")

    role_res = await db.execute(select(Role).where(Role.id == body.role_id))
    role = role_res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found.")

    new_user = User(
        email=body.email.lower(),
        username=body.username,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role_id=body.role_id,
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    await record_audit_event(
        db,
        action="user.create",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="user",
        entity_id=new_user.id,
        request=request,
    )
    await db.commit()

    return UserDetailResponse(
        id=str(new_user.id),
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        role_name=role.name,
        role_display=role.display_name,
        is_active=new_user.is_active,
        mfa_enabled=new_user.mfa_enabled,
        created_at=new_user.created_at,
    )


@router.patch("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update user information, activate/deactivate, or modify role."""
    res = await db.execute(select(User).where(User.id == user_id).options(selectinload(User.role)))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")

    if body.full_name is not None:
        u.full_name = body.full_name
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.role_id is not None:
        role_res = await db.execute(select(Role).where(Role.id == body.role_id))
        role = role_res.scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found.")
        u.role_id = body.role_id
        u.role = role

    await db.flush()
    await record_audit_event(
        db,
        action="user.update",
        outcome="success",
        actor_id=current_user.id,
        actor_username=current_user.username,
        entity_type="user",
        entity_id=u.id,
        request=request,
    )
    await db.commit()

    return UserDetailResponse(
        id=str(u.id),
        email=u.email,
        username=u.username,
        full_name=u.full_name,
        role_name=u.role.name if u.role else None,
        role_display=u.role.display_name if u.role else None,
        is_active=u.is_active,
        mfa_enabled=u.mfa_enabled,
        created_at=u.created_at,
    )
