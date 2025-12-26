from __future__ import annotations

from typing import List

from pydantic import BaseModel, EmailStr

from app.models.entities import StaffRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: StaffRole


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: StaffRole


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: List[str] = []


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    scopes: List[str]
    active: bool
    key: str | None = None  # returned only on creation

