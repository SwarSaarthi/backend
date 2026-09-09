"""
SwarSaarthi — FastAPI Main Application Entrypoint
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import engine
from app.models.base import Base
import app.models  # noqa: F401 to load all models for metadata

from app.api.auth import router as auth_router
from app.api.words import router as words_router
from app.api.practice import router as practice_router
from app.api.profile import router as profile_router
from app.api.asr_router import router as asr_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Load the ASR model at startup (Option B — instant first prediction)
    logger.info("Loading ASR model at startup…")
    try:
        from app.services.asr import load_model
        load_model()
    except Exception as e:
        logger.error("Failed to load ASR model: %s", e)
        logger.warning("ASR predictions will be unavailable until the model is loaded.")

    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Routers ───────────────────────────────────────
app.include_router(auth_router)
app.include_router(words_router)
app.include_router(practice_router)
app.include_router(profile_router)
app.include_router(asr_router)


@app.get("/api/health", tags=["health"])
async def health_check():
    from app.services.asr import is_model_loaded
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "asr_model_loaded": is_model_loaded(),
    }

