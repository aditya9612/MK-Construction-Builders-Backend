from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import register_logging
from app.core.media_settings import get_media_settings


class MediaCORSMiddleware(BaseHTTPMiddleware):
    """Public images must be readable by the static website even when Origin is omitted."""

    def __init__(self, app, url_prefix: str):
        super().__init__(app)
        self.url_prefix = url_prefix.rstrip("/") or "/media"

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(self.url_prefix):
            response.headers.setdefault("Access-Control-Allow-Origin", "*")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
        return response


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="MK Construction & Builders quotation and estimation API",
    docs_url="/docs",
    redoc_url="/redoc",
)

register_logging(app)
register_exception_handlers(app)

media_settings = get_media_settings()
media_settings.media_root.mkdir(parents=True, exist_ok=True)

app.add_middleware(MediaCORSMiddleware, url_prefix=media_settings.url_prefix)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.mount(
    media_settings.url_prefix,
    StaticFiles(directory=str(media_settings.media_root)),
    name="media",
)



@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"], summary="Database health check")
async def health_db():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
