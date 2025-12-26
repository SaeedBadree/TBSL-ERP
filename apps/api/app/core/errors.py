import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def problem_response(
    status: int,
    title: str,
    detail: Any | None = None,
    type_: str = "about:blank",
) -> dict[str, Any]:
    """Build a simple Problem Details (RFC 7807) response payload."""
    return {"type": type_, "title": title, "status": status, "detail": detail or title}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    payload = problem_response(
        status=exc.status_code,
        title=exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__,
        detail=exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    payload = problem_response(status=422, title="Validation Error", detail=exc.errors())
    return JSONResponse(status_code=422, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    payload = problem_response(status=500, title="Internal Server Error")
    return JSONResponse(status_code=500, content=payload)


def add_exception_handlers(app: FastAPI) -> None:
    """Register shared exception handlers on the FastAPI app."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


