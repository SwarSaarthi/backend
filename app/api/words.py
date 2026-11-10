"""
SwarSaarthi — Words API

GET  /api/words           — list words with optional difficulty/category filter
GET  /api/words/random    — get N random words (any difficulty)
GET  /api/words/{word_id} — get a single word by ID
GET  /api/words/categories — list all unique categories
"""

import random as py_random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.word import Word, WordRead

router = APIRouter(prefix="/api/words", tags=["words"])


@router.get("", response_model=list[WordRead])
async def list_words(
    difficulty: str | None = Query(None, description="basic | intermediate | advanced"),
    category: str | None = Query(None),
    item_type: str | None = Query(None, description="word | sentence"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Word)
    if item_type:
        stmt = stmt.where(Word.item_type == item_type)
    if difficulty:
        stmt = stmt.where(Word.difficulty == difficulty)
    if category:
        stmt = stmt.where(Word.category == category)
    stmt = stmt.order_by(Word.text_hi).offset(offset).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/random", response_model=list[WordRead])
async def random_words(
    count: int = Query(10, ge=1, le=50),
    difficulty: str | None = Query(None),
    item_type: str | None = Query(None, description="word | sentence"),
    db: AsyncSession = Depends(get_db),
):
    """Return N randomly selected items (words or sentences)."""
    stmt = select(Word)
    if item_type:
        stmt = stmt.where(Word.item_type == item_type)
    if difficulty:
        stmt = stmt.where(Word.difficulty == difficulty)
    stmt = stmt.order_by(func.random()).limit(count)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/categories", response_model=list[str])
async def list_categories(
    item_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Word.category).distinct()
    if item_type:
        stmt = stmt.where(Word.item_type == item_type)
    result = await db.execute(stmt.order_by(Word.category))
    return [row[0] for row in result.all()]


@router.get("/count")
async def word_counts(
    item_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return item counts grouped by difficulty."""
    stmt = select(Word.difficulty, func.count(Word.id))
    if item_type:
        stmt = stmt.where(Word.item_type == item_type)
    result = await db.execute(stmt.group_by(Word.difficulty))
    counts = {row[0]: row[1] for row in result.all()}
    counts["total"] = sum(counts.values())
    return counts


@router.get("/{word_id}", response_model=WordRead)
async def get_word(word_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")
    return word
