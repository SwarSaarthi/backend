"""
SwarSaarthi — Practice Models

PracticeSession — one recording attempt
UserWordProgress — aggregated per-word stats (focus words, avg accuracy)
UserStreak — one row per day the user practiced
"""

import uuid
from datetime import datetime, timezone, date
from sqlalchemy import String, Float, Integer, Boolean, Date, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PracticeSession(Base):
    """A single pronunciation attempt."""
    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_text: Mapped[str] = mapped_column(String(500), nullable=False)
    recognized_text: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phoneme_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserWordProgress(Base):
    """Per-word aggregated progress for a user."""
    __tablename__ = "user_word_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("words.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    best_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    needs_focus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class UserStreak(Base):
    """One row per day the user practiced — used for calendar heatmap & streak counting."""
    __tablename__ = "user_streaks"
    __table_args__ = (
        UniqueConstraint("user_id", "practice_date", name="uq_user_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    practice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    words_practiced_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
