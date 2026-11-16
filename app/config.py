"""
SwarSaarthi — Application Settings

Loads configuration from environment variables / .env file.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "SwarSaarthi Backend API"

    # ── Database ──────────────────────────────────────────────
    # Defaults to SQLite async for zero-config local development,
    # or override with DATABASE_URL for Neon PostgreSQL.
    DATABASE_URL: str = "sqlite+aiosqlite:///./swarsaarthi.db"

    # ── JWT Authentication ────────────────────────────────────
    JWT_SECRET: str = Field(..., min_length=32, repr=False)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value.strip()) < 32 or value == "swarsaarthi-super-secret-jwt-key-2026":
            raise ValueError("JWT_SECRET must be a new, randomly generated secret of at least 32 characters")
        return value

    # ── Hugging Face Token (for gated models like ai4bharat/indicwav2vec-hindi) ────
    HF_TOKEN: str = ""

    # ── Google Gemini API Key (for AI pronunciation feedback) ─
    SWAR_GOOGLE_KEY: str = ""

    # ── Groq API Key (Free ultra-fast fallback LLM for live presentations) ──
    GROQ_API_KEY: str = ""
    VOICE_GEMINI_MODEL: str = "gemini-3.8-flash"
    VOICE_GROQ_MODEL: str = "qwen/qwen3.8-27b"

    # ── CORS ──────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [ 
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "hide_input_in_errors": True,
    }


settings = Settings()
