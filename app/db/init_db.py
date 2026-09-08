"""
SwarSaarthi — Database Initialization & Migration Script

Creates all database tables (users, words, practice_sessions, user_word_progress, user_streaks)
and seeds initial vocabulary dataset.
"""

import asyncio
import sys
from app.db.session import engine
from app.models.base import Base
import app.models  # Register all models with Base.metadata
from app.db.seed_words import seed_words


async def init_db():
    print("[*] Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[+] Tables initialized successfully.")

    print("[*] Running word dataset seed...")
    await seed_words()
    print("[+] Database ready!")


if __name__ == "__main__":
    asyncio.run(init_db())
