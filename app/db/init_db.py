"""
SwarSaarthi — Database Initialization & Migration Script

Creates all database tables (users, words, practice_sessions, user_word_progress, user_streaks)
and seeds initial vocabulary dataset.
"""

import asyncio
from app.db.session import engine
from app.db.schema import create_schema
from app.db.seed_words import seed_words
from app.db.seed_sentences import seed_sentences


async def init_db():
    print("[*] Initializing database tables...")
    await create_schema(engine)
    print("[+] Tables initialized successfully.")

    print("[*] Running word dataset seed...")
    await seed_words()
    print("[*] Running sentence dataset seed...")
    await seed_sentences()
    print("[+] Database ready!")


if __name__ == "__main__":
    asyncio.run(init_db())
