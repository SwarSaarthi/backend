"""Create tables and preserve compatibility with databases predating sentence practice."""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

import app.models  # noqa: F401 - register all tables
from app.models.base import Base


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        columns = await conn.run_sync(lambda connection: inspect(connection).get_columns("words"))
        if not any(column["name"] == "item_type" for column in columns):
            await conn.execute(text(
                "ALTER TABLE words ADD COLUMN item_type VARCHAR(20) NOT NULL DEFAULT 'word'"
            ))
        await conn.execute(text("UPDATE words SET item_type = 'word' WHERE item_type IS NULL"))
