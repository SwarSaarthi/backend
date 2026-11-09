"""
SwarSaarthi — High Performance Text-to-Speech (TTS) Service

Provides fast, natural-sounding audio synthesis for:
1. Single Hindi vocabulary words (sub-second latency via Google TTS engine)
2. Detailed articulation feedback from Gemini AI (via Microsoft Neural Voices)
3. In-memory LRU caching to make repeat requests instantaneous (< 5ms).
"""

import hashlib
import logging
import re
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

# ── In-Memory Cache for fast repeated playback ──────────────
# key: md5(f"{text}:{lang}:{rate}"), value: bytes (audio/mpeg)
_TTS_CACHE: dict[str, bytes] = {}
_MAX_CACHE_SIZE = 1000


def _get_cache_key(text: str, lang: str, rate: float) -> str:
    raw = f"{text.strip().lower()}:{lang}:{round(rate, 2)}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _has_devanagari(text: str) -> bool:
    """Check if the text contains Devanagari characters (U+0900 to U+097F)."""
    return bool(re.search(r"[\u0900-\u097F]", text))


# ── Google Fast Web TTS (Optimized for short phrases < 200 chars) ───
async def _synthesize_google_fast(text: str, lang: str = "hi") -> Optional[bytes]:
    """
    Synthesize audio using Google's lightweight TTS endpoint.
    Typically resolves in 200-400ms for single Hindi words.
    """
    url = "https://translate.google.com/translate_tts"
    # Clean text of markdown and excessive whitespace
    clean_text = re.sub(r"[*_#`~>\[\]]", "", text).strip()
    # Limit to 200 characters per Google endpoint constraint
    if len(clean_text) > 200:
        clean_text = clean_text[:200]

    params = {
        "ie": "UTF-8",
        "q": clean_text,
        "tl": lang,
        "client": "tw-ob",
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(url, params=params, headers=headers)
            if res.status_code == 200 and len(res.content) > 500:
                return res.content
            logger.warning("Google Fast TTS returned status %d", res.status_code)
    except Exception as e:
        logger.warning("Google Fast TTS request failed: %s", e)
    return None


# ── Microsoft Edge Neural TTS (Natural long-form speech) ────────────
async def _synthesize_edge_neural(
    text: str,
    voice: str,
    rate_str: str = "+0%",
) -> Optional[bytes]:
    """
    Synthesize audio using Edge Neural TTS.
    Produces high-fidelity broadcast quality audio.
    """
    try:
        import edge_tts

        # Strip markdown symbols so speech reads naturally
        clean_text = re.sub(r"[*_#`~>\[\]]", "", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        communicate = edge_tts.Communicate(clean_text, voice=voice, rate=rate_str)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        if chunks:
            return b"".join(chunks)
    except Exception as e:
        logger.warning("Edge Neural TTS failed for voice '%s': %s", voice, e)
    return None


# ── Public API ──────────────────────────────────────────────────────
async def synthesize_speech(
    text: str,
    lang: str = "hi",
    speed: float = 0.85,
) -> Optional[bytes]:
    """
    Generate MP3 speech bytes for the given text.

    Args:
        text: Hindi or English text to speak
        lang: Target language ('hi' or 'en')
        speed: Playback speed (0.5 to 1.5, default 0.85 for articulation clarity)

    Returns:
        MP3 audio bytes, or None if synthesis failed.
    """
    if not text or not text.strip():
        return None

    cleaned_text = text.strip()
    cache_key = _get_cache_key(cleaned_text, lang, speed)

    # 1. Return cached audio if present
    if cache_key in _TTS_CACHE:
        return _TTS_CACHE[cache_key]

    audio_bytes: Optional[bytes] = None

    # Calculate Edge rate string: speed=1.0 -> "+0%", speed=0.75 -> "-25%"
    speed_percent = int(round((speed - 1.0) * 100))
    rate_str = f"{speed_percent:+d}%"

    is_devanagari = _has_devanagari(cleaned_text)

    # Strategy:
    # A. For single words or short phrases (<= 120 chars) in Hindi, Google Fast TTS
    #    is virtually instantaneous (200-400ms).
    if len(cleaned_text) <= 120 and (lang == "hi" or is_devanagari):
        audio_bytes = await _synthesize_google_fast(cleaned_text, lang="hi")

    # B. If not short Hindi or Google Fast failed, use Microsoft Neural Voice
    if not audio_bytes:
        voice = "hi-IN-SwaraNeural" if (lang == "hi" or is_devanagari) else "en-IN-NeerjaNeural"
        audio_bytes = await _synthesize_edge_neural(cleaned_text, voice=voice, rate_str=rate_str)

    # C. Final fallback if Edge Neural failed
    if not audio_bytes and len(cleaned_text) <= 200:
        audio_bytes = await _synthesize_google_fast(cleaned_text, lang="hi" if is_devanagari else "en")

    # Cache successful audio
    if audio_bytes:
        if len(_TTS_CACHE) >= _MAX_CACHE_SIZE:
            # Evict first 200 keys
            keys_to_remove = list(_TTS_CACHE.keys())[:200]
            for k in keys_to_remove:
                _TTS_CACHE.pop(k, None)
        _TTS_CACHE[cache_key] = audio_bytes
        return audio_bytes

    logger.error("All TTS synthesis strategies failed for text: '%s'", cleaned_text[:30])
    return None

