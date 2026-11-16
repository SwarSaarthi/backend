"""Authenticated voice conversation endpoints; no recordings are retained."""
import json
import os
import tempfile
import threading
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError
from starlette.concurrency import run_in_threadpool
from app.core.deps import get_current_user
from app.models.user import User
from app.services.voice_conversation import reply_to_turn

router = APIRouter(prefix="/api/voice", tags=["voice"])
_inference_lock = threading.Lock()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    history: list[Message] = Field(default_factory=list, max_length=12)


async def respond(payload: ChatRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(422, "Please say or type a message first.")
    try:
        result = await reply_to_turn([m.model_dump() for m in payload.history], text)
        return {"transcript": text, **result}
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from error


@router.post("/chat")
async def chat(payload: ChatRequest, user: User = Depends(get_current_user)):
    return await respond(payload)


def transcribe(path: str) -> str:
    from app.services.asr import predict_audio
    # The locally loaded model is shared; serialize voice inference calls.
    with _inference_lock:
        return predict_audio(path)


@router.post("/turn")
async def voice_turn(audio: UploadFile = File(...), history: str = Form("[]"), user: User = Depends(get_current_user)):
    from app.services.asr import is_model_loaded
    if not is_model_loaded():
        raise HTTPException(503, "Speech recognition is still loading. Try typing a message while it starts.")
    if len(history) > 80000:
        raise HTTPException(422, "Conversation history is too long.")
    try:
        payload = ChatRequest(text="pending", history=json.loads(history))
    except (ValueError, TypeError, ValidationError):
        raise HTTPException(422, "Invalid conversation history.")
    content = await audio.read(12 * 1024 * 1024 + 1)
    if not content or len(content) > 12 * 1024 * 1024:
        raise HTTPException(413, "Please record a short message, up to 30 seconds.")
    suffix = os.path.splitext(audio.filename or "voice.webm")[1].lower()
    if suffix not in {".webm", ".wav", ".ogg", ".m4a", ".mp4"}:
        suffix = ".webm"
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as target:
            target.write(content)
        try:
            text = await run_in_threadpool(transcribe, path)
        except Exception as error:
            raise HTTPException(422, "We couldn’t read this recording. Please try again or type your message.") from error
        if not text.strip():
            raise HTTPException(422, "No speech was recognized. Please speak a little closer to the microphone.")
        if len(text) > 2000:
            raise HTTPException(422, "Please split your message into shorter turns.")
        payload.text = text
        return await respond(payload)
    finally:
        if os.path.exists(path):
            os.remove(path)
