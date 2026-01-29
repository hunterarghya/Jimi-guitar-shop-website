"""Error handling middleware."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from typing import Union

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Application-level exception."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.detail)


async def http_exception_handler(request: Request, exc: Exception):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {str(exc)}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions."""
    logger.warning(f"Validation Error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


async def app_exception_handler(request: Request, exc: AppException):
    """Handle application exceptions."""
    logger.warning(f"App Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
