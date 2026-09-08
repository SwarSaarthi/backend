"""
SwarSaarthi — Models __init__

Import all models so SQLAlchemy's metadata.create_all() picks them up.
"""

from app.models.base import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.word import Word  # noqa: F401
from app.models.practice import PracticeSession, UserWordProgress, UserStreak  # noqa: F401
