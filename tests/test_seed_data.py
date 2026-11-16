import os
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

with patch.dict(os.environ, {
    "JWT_SECRET": "test-only-signing-secret-with-at-least-32-characters",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
}):
    from app.db import init_db, seed_sentences, seed_words
    from app.models.word import Word


class DatasetTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.patches = ExitStack()
        for module in (init_db, seed_words, seed_sentences):
            self.patches.enter_context(patch.object(module, "engine", self.engine))
        for module in (seed_words, seed_sentences):
            self.patches.enter_context(patch.object(module, "async_session_factory", self.sessions))

    async def asyncTearDown(self):
        self.patches.close()
        await self.engine.dispose()

    async def test_initialization_seeds_both_datasets_without_duplicates(self):
        await init_db.init_db()
        async with self.sessions() as session:
            first = (await session.execute(select(Word))).scalars().all()
            first_ids = {word.id for word in first}
            self.assertEqual(
                {word.text_hi for word in first if word.item_type == "word"},
                {item["text_hi"] for item in seed_words.WORDS_DATA},
            )
            self.assertEqual(
                {word.text_hi for word in first if word.item_type == "sentence"},
                {item["text_hi"] for item in seed_sentences.SENTENCES_DATA},
            )

        await init_db.init_db()
        async with self.sessions() as session:
            second = (await session.execute(select(Word))).scalars().all()
            self.assertEqual(len(second), len(first))
            self.assertEqual({word.id for word in second}, first_ids)

    async def test_sentence_seed_updates_existing_records_without_changing_ids(self):
        await init_db.init_db()
        text = seed_sentences.SENTENCES_DATA[0]["text_hi"]
        async with self.sessions() as session:
            word = (await session.execute(select(Word).where(Word.text_hi == text))).scalar_one()
            original_id = word.id
            word.meaning_en = "Outdated meaning"
            word.item_type = "word"
            await session.commit()

        await seed_sentences.seed_sentences()
        async with self.sessions() as session:
            word = (await session.execute(select(Word).where(Word.text_hi == text))).scalar_one()
            self.assertEqual(word.id, original_id)
            self.assertEqual(word.item_type, "sentence")
            self.assertEqual(word.meaning_en, seed_sentences.SENTENCES_DATA[0]["meaning_en"])

    async def test_initialization_upgrades_legacy_word_table(self):
        async with self.engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE words (
                    id VARCHAR(36) PRIMARY KEY, text_hi VARCHAR(500) NOT NULL,
                    transliteration VARCHAR(500) NOT NULL, meaning_en VARCHAR(500) NOT NULL,
                    meaning_hi VARCHAR(500) NOT NULL, difficulty VARCHAR(20) NOT NULL,
                    category VARCHAR(100) NOT NULL, audio_url VARCHAR(500)
                )
            """))
            await conn.execute(text("""
                INSERT INTO words (id, text_hi, transliteration, meaning_en, meaning_hi, difficulty, category)
                VALUES ('legacy-word', 'पुराना', 'Purana', 'Old', '', 'basic', 'Test')
            """))

        await init_db.init_db()
        async with self.sessions() as session:
            legacy = await session.get(Word, "legacy-word")
            self.assertEqual(legacy.item_type, "word")
            self.assertEqual(legacy.text_hi, "पुराना")
            sentences = (await session.execute(select(Word).where(Word.item_type == "sentence"))).scalars().all()
            self.assertEqual(len(sentences), len(seed_sentences.SENTENCES_DATA))


if __name__ == "__main__":
    unittest.main()
