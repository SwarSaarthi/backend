"""
SwarSaarthi — Text-to-Speech (TTS) API Router

GET  /api/tts?text=...&lang=...&speed=...
POST /api/tts (JSON body with text, lang, speed)

Returns audio/mpeg stream for fast, responsive playback on frontend.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from app.services.tts_service import synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to synthesize")
    lang: str = Field("hi", description="Language code: 'hi' or 'en'")
    speed: float = Field(0.85, ge=0.5, le=1.5, description="Playback speed")


@router.get("", summary="Synthesize speech (GET)")
async def get_tts(
    text: str = Query(..., min_length=1, max_length=500, description="Text to speak"),
    lang: str = Query("hi", description="Language: 'hi' or 'en'"),
    speed: float = Query(0.85, ge=0.5, le=1.5, description="Speed rate"),
):
    """
    Synthesize audio on-the-fly and return an audio/mpeg stream.
    Optimized with caching for sub-5ms repeated response times.
    """
    audio_bytes = await synthesize_speech(text=text, lang=lang, speed=speed)
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synthesize speech for the requested text.",
        )

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": "inline; filename=\"speech.mp3\"",
        },
    )


@router.post("", summary="Synthesize speech (POST for longer text)")
async def post_tts(payload: TtsRequest):
    """
    Synthesize audio for longer text (such as Gemini coaching feedback).
    """
    audio_bytes = await synthesize_speech(
        text=payload.text,
        lang=payload.lang,
        speed=payload.speed,
    )
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synthesize speech for the requested text.",
        )

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": "inline; filename=\"speech.mp3\"",
        },
    )

