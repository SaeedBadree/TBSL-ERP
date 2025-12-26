from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.security import create_access_token, require_roles, verify_password
from app.models.entities import ApiKey, StaffRole, StaffUser
from app.schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyResponse,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from app.core.security import generate_api_key, hash_api_key, get_current_user

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(StaffUser).where(StaffUser.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=UserResponse)
async def me(current_user: StaffUser = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
    )


@router.post("/admin/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    payload: ApiKeyCreateRequest,
    session: AsyncSession = Depends(get_session),
    _: StaffUser = Depends(require_roles([StaffRole.ADMIN])),
):
    raw_key, key_hash = generate_api_key()
    api_key = ApiKey(name=payload.name, key_hash=key_hash, scopes=payload.scopes, active=True)
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return ApiKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        scopes=api_key.scopes,
        active=api_key.active,
        key=raw_key,
    )


@router.delete("/admin/api-keys/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: str,
    session: AsyncSession = Depends(get_session),
    _: StaffUser = Depends(require_roles([StaffRole.ADMIN])),
):
    result = await session.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    api_key.active = False
    session.add(api_key)
    await session.commit()
    return None

