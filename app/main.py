from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import register_logging

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="MK Construction & Builders quotation and estimation API",
    docs_url="/docs",
    redoc_url="/redoc",
)

register_logging(app)
register_exception_handlers(app)

cors_origins = settings.cors_origin_list
if settings.is_production and ("*" in cors_origins or not cors_origins):
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["Health"], summary="Database health check")
async def health_db():
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
