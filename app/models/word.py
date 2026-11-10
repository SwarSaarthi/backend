"""
SwarSaarthi — Word Model & Pydantic Schemas

Each word is a Hindi speech practice item categorized by difficulty.
audio_url is optional — frontend defaults to browser Web Speech API.
"""

import uuid
import enum
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel

from app.models.base import Base


class Difficulty(str, enum.Enum):
    basic = "basic"
    intermediate = "intermediate"
    advanced = "advanced"


class Word(Base):
    __tablename__ = "words"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    text_hi: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    transliteration: Mapped[str] = mapped_column(String(500), nullable=False)
    meaning_en: Mapped[str] = mapped_column(String(500), nullable=False)
    meaning_hi: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    difficulty: Mapped[str] = mapped_column(
        Enum(Difficulty, name="difficulty_enum", create_constraint=True),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    item_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="word", server_default="word", index=True
    )


# ── Pydantic Schemas ─────────────────────────────────────────

class WordRead(BaseModel):
    id: str
    text_hi: str
    transliteration: str
    meaning_en: str
    meaning_hi: str
    difficulty: str
    category: str
    audio_url: str | None = None
    item_type: str = "word"

    model_config = {"from_attributes": True}


class WordListParams(BaseModel):
    """Query parameters for filtering words."""
    difficulty: str | None = None
    category: str | None = None
    item_type: str | None = None
    limit: int = 20
    offset: int = 0
