"""
SwarSaarthi — Profile API

GET /api/profile                 — Overall profile dashboard stats
GET /api/profile/focus-words     — Words that need extra practice
GET /api/profile/streak-calendar — Daily practice activity heatmap
GET /api/profile/progress        — Difficulty-wise progress statistics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.word import Word
from app.models.practice import PracticeSession, UserWordProgress, UserStreak
from app.services.streak_calculator import get_streak_info, get_streak_calendar

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("")
async def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Streak Info
    streak_info = await get_streak_info(db, current_user.id)

    # 2. Total words attempted & overall avg accuracy
    stats_result = await db.execute(
        select(
            func.count(UserWordProgress.id),
            func.coalesce(func.avg(UserWordProgress.avg_accuracy), 0.0),
            func.coalesce(func.sum(UserWordProgress.total_attempts), 0),
        ).where(UserWordProgress.user_id == current_user.id)
    )
    words_attempted, overall_avg, total_attempts = stats_result.one()

    # 3. Focus words count
    focus_count_res = await db.execute(
        select(func.count(UserWordProgress.id)).where(
            UserWordProgress.user_id == current_user.id,
            UserWordProgress.needs_focus == True,
        )
    )
    focus_words_count = focus_count_res.scalar() or 0

    # 4. Total available words
    total_words_res = await db.execute(select(func.count(Word.id)))
    total_words_available = total_words_res.scalar() or 0

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "streak": {
            "current_streak": streak_info["current_streak"],
            "longest_streak": streak_info["longest_streak"],
            "total_practice_days": streak_info["total_practice_days"],
        },
        "stats": {
            "unique_words_practiced": words_attempted,
            "total_attempts": total_attempts,
            "overall_accuracy": round(float(overall_avg), 1),
            "focus_words_count": focus_words_count,
            "total_words_available": total_words_available,
        },
    }


@router.get("/focus-words")
async def get_focus_words(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(UserWordProgress, Word)
        .join(Word, UserWordProgress.word_id == Word.id)
        .where(
            UserWordProgress.user_id == current_user.id,
            UserWordProgress.needs_focus == True,
        )
        .order_by(UserWordProgress.avg_accuracy.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for prog, word in rows:
        items.append({
            "word_id": word.id,
            "item_type": word.item_type,
            "text_hi": word.text_hi,
            "transliteration": word.transliteration,
            "meaning_en": word.meaning_en,
            "category": word.category,
            "difficulty": word.difficulty,
            "total_attempts": prog.total_attempts,
            "correct_attempts": prog.correct_attempts,
            "avg_accuracy": prog.avg_accuracy,
            "best_score": prog.best_score,
            "last_practiced_at": prog.last_practiced_at.isoformat() if prog.last_practiced_at else None,
        })

    return {"focus_words": items, "count": len(items)}


@router.get("/streak-calendar")
async def get_calendar_data(
    days: int = Query(180, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    calendar = await get_streak_calendar(db, current_user.id, days=days)
    return {"calendar": calendar}


@router.get("/progress")
async def get_difficulty_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get total words per difficulty
    totals_res = await db.execute(
        select(Word.difficulty, func.count(Word.id)).group_by(Word.difficulty)
    )
    totals = {row[0]: row[1] for row in totals_res.all()}

    # Get attempted count & avg score per difficulty for current user
    user_prog_res = await db.execute(
        select(
            Word.difficulty,
            func.count(UserWordProgress.id),
            func.coalesce(func.avg(UserWordProgress.avg_accuracy), 0.0),
            func.count(UserWordProgress.id).filter(UserWordProgress.avg_accuracy >= 70.0),
        )
        .join(Word, UserWordProgress.word_id == Word.id)
        .where(UserWordProgress.user_id == current_user.id)
        .group_by(Word.difficulty)
    )
    user_stats = {
        row[0]: {
            "attempted": row[1],
            "avg_accuracy": round(float(row[2]), 1),
            "mastered": row[3],
        }
        for row in user_prog_res.all()
    }

    difficulties = ["basic", "intermediate", "advanced"]
    breakdown = {}
    for diff in difficulties:
        tot = totals.get(diff, 0)
        u = user_stats.get(diff, {"attempted": 0, "avg_accuracy": 0.0, "mastered": 0})
        pct = round((u["attempted"] / tot * 100), 1) if tot > 0 else 0.0
        breakdown[diff] = {
            "total_words": tot,
            "attempted_words": u["attempted"],
            "mastered_words": u["mastered"],
            "avg_accuracy": u["avg_accuracy"],
            "completion_percentage": pct,
        }

    return {"breakdown": breakdown}
