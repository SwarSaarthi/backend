"""
SwarSaarthi — Streak Calculator

Determines the user's current consecutive-day streak, longest streak,
and provides calendar heatmap data from the user_streaks table.
"""

from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import UserStreak


async def get_streak_info(db: AsyncSession, user_id: str) -> dict:
    """
    Returns:
      - current_streak: int (consecutive days ending today or yesterday)
      - longest_streak: int
      - total_practice_days: int
    """
    result = await db.execute(
        select(UserStreak.practice_date)
        .where(UserStreak.user_id == user_id)
        .order_by(UserStreak.practice_date.desc())
    )
    dates_desc: list[date] = [row[0] for row in result.all()]

    if not dates_desc:
        return {"current_streak": 0, "longest_streak": 0, "total_practice_days": 0}

    today = date.today()

    # ── Current streak ────────────────────────────────────────
    current = 0
    # Allow streak to count if last practice was today or yesterday
    expected = today
    if dates_desc[0] == today - timedelta(days=1):
        expected = today - timedelta(days=1)

    for d in dates_desc:
        if d == expected:
            current += 1
            expected -= timedelta(days=1)
        elif d < expected:
            break

    # ── Longest streak ────────────────────────────────────────
    dates_asc = sorted(dates_desc)
    longest = 1
    run = 1
    for i in range(1, len(dates_asc)):
        if dates_asc[i] == dates_asc[i - 1] + timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return {
        "current_streak": current,
        "longest_streak": longest,
        "total_practice_days": len(dates_desc),
    }


async def get_streak_calendar(db: AsyncSession, user_id: str, days: int = 180) -> list[dict]:
    """
    Returns a list of { date, words_practiced_count } for the last N days.
    Used by the frontend calendar heatmap component.
    """
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(UserStreak.practice_date, UserStreak.words_practiced_count)
        .where(UserStreak.user_id == user_id, UserStreak.practice_date >= since)
        .order_by(UserStreak.practice_date)
    )
    return [
        {"date": str(row[0]), "count": row[1]}
        for row in result.all()
    ]
