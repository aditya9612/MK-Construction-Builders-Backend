from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

UNPROCESSABLE = status.HTTP_422_UNPROCESSABLE_CONTENT


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Request failed"

    def __init__(self, message: str | None = None, errors: list[dict] | None = None):
        self.message = message or self.message
        self.errors = errors or []
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Unauthorized"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    message = "Forbidden"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    message = "Conflict"


class ValidationFailedError(AppError):
    status_code = UNPROCESSABLE
    message = "Validation failed"


class DatabaseError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "A database error occurred"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "errors": exc.errors,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
            errors.append({"field": loc, "message": err.get("msg")})
        return JSONResponse(
            status_code=UNPROCESSABLE,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": errors,
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("integrity_error", extra={"detail": str(exc.orig) if exc.orig else "constraint"})
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": "A uniqueness or integrity constraint was violated",
                "errors": [],
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("database_error")
        message = "A database error occurred"
        if settings.debug and not settings.is_production:
            message = "A database error occurred"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": message, "errors": []},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, AppError):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "message": exc.message,
                    "errors": exc.errors,
                },
            )
        logger.exception("unhandled_error")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected error occurred",
                "errors": [],
            },
        )
