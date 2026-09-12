"""
SwarSaarthi — ASR API Router

POST /api/asr/predict
    Accepts an audio file (any browser format) + word_id,
    runs IndicWav2Vec ASR, evaluates pronunciation, persists the
    practice session, and returns structured feedback.
"""

import os
import tempfile
import logging
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.word import Word
from app.models.practice import PracticeSession, UserWordProgress, UserStreak
from app.services.asr import predict_audio, analyze_pronunciation, is_model_loaded

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["asr"])


@router.post("/predict")
async def asr_predict(
    audio: UploadFile = File(..., description="Audio recording (WebM/WAV/OGG)"),
    word_id: str = Form(..., description="Target word UUID from the words table"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full ASR pipeline:
      1. Save uploaded audio to a temp file
      2. Run IndicWav2Vec → get predicted Hindi text
      3. Evaluate prediction vs target (CER + rapidfuzz accuracy)
      4. Persist PracticeSession + update UserWordProgress + UserStreak
      5. Return rich feedback payload
    """

    # ── 0. Pre-flight ────────────────────────────────────────────
    if not is_model_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ASR model is still loading. Please wait a moment and try again.",
        )

    # ── 1. Fetch target word ─────────────────────────────────────
    result = await db.execute(select(Word).where(Word.id == word_id))
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found",
        )

    # ── 2. Save uploaded audio to a temp file ────────────────────
    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(temp_fd, "wb") as f:
            content = await audio.read()
            f.write(content)

        # ── 3. ASR Prediction ────────────────────────────────────
        prediction_text = predict_audio(temp_path)
        logger.info(
            "ASR prediction for word '%s': '%s' → '%s'",
            word_id, word.text_hi, prediction_text,
        )

        # ── 4. Analyze pronunciation ─────────────────────────────
        analysis = analyze_pronunciation(word.text_hi, prediction_text)

        accuracy = analysis["accuracy_score"]
        is_correct = analysis["is_correct"]

        # ── 5. Persist PracticeSession ───────────────────────────
        practice_session = PracticeSession(
            user_id=current_user.id,
            word_id=word.id,
            target_text=word.text_hi,
            recognized_text=prediction_text,
            accuracy_score=accuracy,
            is_correct=is_correct,
            phoneme_breakdown=analysis["details"],
        )
        db.add(practice_session)

        # ── 6. Upsert UserWordProgress ───────────────────────────
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
            progress.needs_focus = (new_avg < 70.0)
            progress.last_practiced_at = datetime.now(timezone.utc)

        # ── 7. Update today's UserStreak ─────────────────────────
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

        # ── 8. Return response ───────────────────────────────────
        return {
            "session_id": practice_session.id,
            "word_id": word.id,
            "target_text": word.text_hi,
            "prediction_text": prediction_text,
            "accuracy_score": accuracy,
            "cer": analysis["cer"],
            "is_correct": is_correct,
            "feedback_tier": analysis.get(
                "feedback_tier",
                "excellent" if is_correct else ("almost_there" if accuracy >= 50.0 else "needs_improvement")
            ),
            "feedback": analysis["feedback"],
            "details": analysis["details"],
            "needs_focus": progress.needs_focus,
            "streak": today_streak.words_practiced_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("ASR prediction failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ASR prediction failed: {str(e)}",
        )
    finally:
        # Clean up temp audio file
        if os.path.exists(temp_path):
            os.remove(temp_path)
