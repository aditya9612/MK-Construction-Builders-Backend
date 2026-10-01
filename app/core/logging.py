import logging
import sys
import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_logging() -> None:
    level = logging.DEBUG if settings.debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger = get_logger("app.http")
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "%s %s %s %sms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


def register_logging(app: FastAPI) -> None:
    configure_logging()
    app.add_middleware(RequestLoggingMiddleware)
