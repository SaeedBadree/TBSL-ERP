from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import api_key_dependency
from app.models.entities import ApiKey

router = APIRouter()


@router.get("/integrations/orders")
async def create_order(
    api_key: ApiKey = Depends(api_key_dependency(["orders:write"])),
):
    return {"status": "ok", "key": str(api_key.id)}

