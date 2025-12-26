from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Lightweight async CRUD helper."""

    model: Type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, obj_id: Any) -> ModelType | None:
        return await self.session.get(self.model, obj_id)

    async def list(self, offset: int = 0, limit: int = 100) -> Sequence[ModelType]:
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        obj = self.model(**obj_in)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            setattr(obj, field, value)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj


