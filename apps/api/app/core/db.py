from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarative class for ORM models."""


def _create_engine() -> AsyncEngine:
    return create_async_engine(settings.database_url, future=True, echo=False)


engine: AsyncEngine = _create_engine()
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a SQLAlchemy AsyncSession dependency."""
    async with async_session() as session:
        yield session


