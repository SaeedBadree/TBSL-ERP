from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import add_exception_handlers
from app.core.logging import setup_logging
from app.routers import auth as auth_router
from app.routers import integrations as integrations_router
from app.routers import reorder as reorder_router
from app.routers import alerts as alerts_router
from app.services.webhook_service import webhook_worker
from app.core.db import async_session
import asyncio


def create_app() -> FastAPI:
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    add_exception_handlers(app)
    app.include_router(auth_router.router)
    app.include_router(integrations_router.router)
    app.include_router(reorder_router.router)
    app.include_router(alerts_router.router)

    @app.get("/health", summary="Health check")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version", summary="API version")
    async def version() -> dict[str, str]:
        return {"version": settings.version}

    @app.on_event("startup")
    async def start_webhook_worker():
        asyncio.create_task(webhook_worker(async_session))

    return app


app = create_app()


