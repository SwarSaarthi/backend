"""
SwarSaarthi — Practice API

POST /api/practice/submit — Submit a pronunciation attempt & evaluate
GET  /api/practice/history — Get recent practice history for the current user
"""

from datetime import date, datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.word import Word
from app.models.practice import PracticeSession, UserWordProgress, UserStreak
from app.services.nlp_evaluator import evaluate_pronunciation

router = APIRouter(prefix="/api/practice", tags=["practice"])


class PracticeSubmitRequest(BaseModel):
    word_id: str
    recognized_text: str = Field(..., description="Recognized speech text in Hindi / transliterated")


class PracticeSubmitResponse(BaseModel):
    session_id: str
    word_id: str
    target_text: str
    recognized_text: str
    accuracy_score: float
    is_correct: bool
    details: dict
    needs_focus: bool
    streak: int


@router.post("/submit", response_model=PracticeSubmitResponse)
async def submit_practice(
    payload: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch word
    result = await db.execute(select(Word).where(Word.id == payload.word_id))
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

    # 2. Evaluate pronunciation
    evaluation = evaluate_pronunciation(word.text_hi, payload.recognized_text)
    accuracy = evaluation["accuracy"]
    is_correct = evaluation["is_correct"]

    # 3. Create PracticeSession record
    practice_session = PracticeSession(
        user_id=current_user.id,
        word_id=word.id,
        target_text=word.text_hi,
        recognized_text=payload.recognized_text,
        accuracy_score=accuracy,
        is_correct=is_correct,
        phoneme_breakdown=evaluation.get("details"),
    )
    db.add(practice_session)

    # 4. Upsert UserWordProgress
    prog_result = await db.execute(
        select(UserWordProgress).where(
            UserWordProgress.user_id == current_user.id,
            UserWordProgress.word_id == word.id,
        )
    )
    progress = prog_result.scalar_one_or_none()

    if not progress:
        progress = UserWordProgress(
            user_id=current_user.id,
            word_id=word.id,
            total_attempts=1,
            correct_attempts=1 if is_correct else 0,
            avg_accuracy=accuracy,
            best_score=accuracy,
            needs_focus=(accuracy < 70.0),
            last_practiced_at=datetime.now(timezone.utc),
        )
        db.add(progress)
    else:
        new_total = progress.total_attempts + 1
        new_correct = progress.correct_attempts + (1 if is_correct else 0)
        new_avg = round(
            (progress.avg_accuracy * progress.total_attempts + accuracy) / new_total,
            2,
        )
        progress.total_attempts = new_total
        progress.correct_attempts = new_correct
        progress.avg_accuracy = new_avg
        progress.best_score = max(progress.best_score, accuracy)
        # Marked as focus word if average accuracy is below 70%
        progress.needs_focus = (new_avg < 70.0)
        progress.last_practiced_at = datetime.now(timezone.utc)

    # 5. Update or create today's UserStreak record
    today = date.today()
    streak_res = await db.execute(
        select(UserStreak).where(
            UserStreak.user_id == current_user.id,
            UserStreak.practice_date == today,
        )
    )
    today_streak = streak_res.scalar_one_or_none()
    if not today_streak:
        today_streak = UserStreak(
            user_id=current_user.id,
            practice_date=today,
            words_practiced_count=1,
        )
        db.add(today_streak)
    else:
        today_streak.words_practiced_count += 1

    await db.commit()
    await db.refresh(practice_session)

    return PracticeSubmitResponse(
        session_id=practice_session.id,
        word_id=word.id,
        target_text=word.text_hi,
        recognized_text=payload.recognized_text,
        accuracy_score=accuracy,
        is_correct=is_correct,
        details=evaluation["details"],
        needs_focus=progress.needs_focus,
        streak=today_streak.words_practiced_count,
    )


@router.get("/history")
async def practice_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(PracticeSession, Word)
        .join(Word, PracticeSession.word_id == Word.id)
        .where(PracticeSession.user_id == current_user.id)
        .order_by(desc(PracticeSession.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for session, word in rows:
        items.append({
            "id": session.id,
            "word_id": word.id,
            "text_hi": word.text_hi,
            "transliteration": word.transliteration,
            "meaning_en": word.meaning_en,
            "difficulty": word.difficulty,
            "recognized_text": session.recognized_text,
            "accuracy_score": session.accuracy_score,
            "is_correct": session.is_correct,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        })

    return {"items": items, "limit": limit, "offset": offset}
