"""
SwarSaarthi — Application Settings

Loads configuration from environment variables / .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SwarSaarthi Backend API"

    # ── Database ──────────────────────────────────────────────
    # Defaults to SQLite async for zero-config local development,
    # or override with DATABASE_URL for Neon PostgreSQL.
    DATABASE_URL: str = "sqlite+aiosqlite:///./swarsaarthi.db"

    # ── JWT Authentication ────────────────────────────────────
    JWT_SECRET: str = "swarsaarthi-super-secret-jwt-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
