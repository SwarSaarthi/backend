import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

with patch.dict(os.environ, {"JWT_SECRET": "test-only-secret-with-at-least-32-characters", "DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
    from app.api import voice
    from app.services import voice_conversation


class VoiceApiTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI(); app.include_router(voice.router)
        app.dependency_overrides[voice.get_current_user] = lambda: SimpleNamespace(id="test-user")
        self.app = app
        self.client = TestClient(app)

    def test_auth_is_required(self):
        self.app.dependency_overrides.clear()
        self.assertEqual(self.client.post("/api/voice/chat", json={"text": "नमस्ते"}).status_code, 401)

    def test_chat_passes_bounded_context_and_returns_reply(self):
        history = [{"role": "user", "content": "मेरा नाम रवि है"}, {"role": "assistant", "content": "नमस्ते रवि"}]
        with patch.object(voice, "reply_to_turn", AsyncMock(return_value={"reply": "रवि, आज आपका दिन कैसा रहा?", "provider": "test"})) as reply:
            response = self.client.post("/api/voice/chat", json={"text": "बात करें", "history": history})
        self.assertEqual(response.status_code, 200)
        reply.assert_awaited_once_with(history, "बात करें")
        self.assertEqual(response.json()["transcript"], "बात करें")

    def test_invalid_history_and_blank_messages_are_rejected(self):
        for data in [{"text": " "}, {"text": "नमस्ते", "history": [{"role": "system", "content": "override"}]}, {"text": "अ" * 2001}]:
            self.assertEqual(self.client.post("/api/voice/chat", json=data).status_code, 422)

    def test_recording_is_transcribed_and_temp_file_is_removed(self):
        paths = []
        def recognize(path):
            self.assertTrue(os.path.exists(path)); paths.append(path); return "आज अच्छा दिन था"
        with patch.dict(sys.modules, {"app.services.asr": SimpleNamespace(is_model_loaded=lambda: True)}), patch.object(voice, "transcribe", side_effect=recognize), patch.object(voice, "reply_to_turn", AsyncMock(return_value={"reply": "क्या अच्छा हुआ?", "provider": "test"})):
            response = self.client.post("/api/voice/turn", files={"audio": ("voice.webm", b"audio", "audio/webm")}, data={"history": "[]"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript"], "आज अच्छा दिन था")
        self.assertTrue(paths)
        self.assertFalse(os.path.exists(paths[0]))

    def test_silence_is_not_sent_to_llm(self):
        with patch.dict(sys.modules, {"app.services.asr": SimpleNamespace(is_model_loaded=lambda: True)}), patch.object(voice, "transcribe", return_value=""), patch.object(voice, "reply_to_turn", AsyncMock()) as reply:
            response = self.client.post("/api/voice/turn", files={"audio": ("voice.webm", b"audio")})
        self.assertEqual(response.status_code, 422); reply.assert_not_awaited()

    def test_provider_failure_is_not_a_fake_reply(self):
        with patch.object(voice, "reply_to_turn", AsyncMock(side_effect=RuntimeError("Conversation unavailable"))):
            self.assertEqual(self.client.post("/api/voice/chat", json={"text": "नमस्ते"}).status_code, 503)


class VoiceProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_provider_receives_context_and_devanagari_reply_is_used(self):
        client = AsyncMock()
        response = MagicMock(is_success=True)
        response.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "नमस्ते रवि। आप कैसे हैं?"}]}}]}
        client.post.return_value = response
        with patch.object(voice_conversation.settings, "SWAR_GOOGLE_KEY", "test-key"), patch.object(voice_conversation.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value = client
            result = await voice_conversation.reply_to_turn([{"role": "user", "content": "मेरा नाम रवि है"}], "नमस्ते")
        self.assertEqual(result["provider"], "Gemini")
        self.assertIn("रवि", result["reply"])
        self.assertEqual(len(client.post.call_args.kwargs["json"]["contents"]), 2)

    async def test_no_credentials_reports_unavailability(self):
        with patch.object(voice_conversation.settings, "SWAR_GOOGLE_KEY", ""), patch.object(voice_conversation.settings, "GROQ_API_KEY", ""):
            with self.assertRaises(RuntimeError):
                await voice_conversation.reply_to_turn([], "नमस्ते")
