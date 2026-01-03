from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_session
from app.models.entities import ApiKey, StaffRole, StaffUser


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: str, role: StaffRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {"sub": user_id, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    session: AsyncSession = Depends(get_session), authorization: str = Header(None)
) -> StaffUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await session.execute(select(StaffUser).where(StaffUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


def require_roles(roles: Iterable[StaffRole]) -> Callable:
    roles_set = {r for r in roles}

    async def dependency(current_user: StaffUser = Depends(get_current_user)) -> StaffUser:
        if current_user.role not in roles_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return current_user

    return dependency


def hash_api_key(raw_key: str) -> str:
    salted = f"{settings.api_key_salt}:{raw_key}"
    return hashlib.sha256(salted.encode("utf-8")).hexdigest()


async def validate_api_key(
    session: AsyncSession, raw_key: str, scopes_required: list[str]
) -> ApiKey:
    key_hash = hash_api_key(raw_key)
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if scopes_required:
        missing = [s for s in scopes_required if s not in api_key.scopes]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")

    api_key.last_used_at = datetime.now(timezone.utc)
    session.add(api_key)
    await session.commit()
    return api_key


def api_key_dependency(scopes_required: Optional[list[str]] = None):
    scopes_required = scopes_required or []

    async def dependency(
        x_api_key: str = Header(None, alias="X-API-Key"),
        session: AsyncSession = Depends(get_session),
    ) -> ApiKey:
        if not x_api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
        return await validate_api_key(session, x_api_key, scopes_required)

    return dependency


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, key_hash) tuple."""
    raw_key = secrets.token_urlsafe(32)
    return raw_key, hash_api_key(raw_key)



