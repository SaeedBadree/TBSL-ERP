from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_session
from app.core.security import hash_password
from app.main import create_app
from app.models.entities import StaffRole, StaffUser


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def test_app() -> AsyncGenerator[FastAPI, None]:
    app = create_app()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield app
    app.dependency_overrides.clear()
    await engine.dispose()


async def seed_user(app: FastAPI, email: str, password: str, role: StaffRole):
    session_dep = app.dependency_overrides[get_session]
    async for session in session_dep():
        user = StaffUser(
            email=email,
            full_name=email.split("@")[0],
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        return user


@pytest.mark.anyio
async def test_rbac_denial_on_api_key_creation(test_app: FastAPI):
    await seed_user(test_app, "cashier@example.com", "pass123", StaffRole.CASHIER)

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "cashier@example.com", "password": "pass123"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        resp = await client.post(
            "/admin/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "site", "scopes": ["catalog:read"]},
        )
        assert resp.status_code == 403


@pytest.mark.anyio
async def test_api_key_scope_denial(test_app: FastAPI):
    await seed_user(test_app, "admin@example.com", "adminpass", StaffRole.ADMIN)

    async with AsyncClient(app=test_app, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "admin@example.com", "password": "adminpass"})
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        resp = await client.post(
            "/admin/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "reader", "scopes": ["catalog:read"]},
        )
        assert resp.status_code == 200
        api_key = resp.json()["key"]

        resp = await client.get("/integrations/orders", headers={"X-API-Key": api_key})
        assert resp.status_code == 403

