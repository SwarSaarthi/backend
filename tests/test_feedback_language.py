import unittest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.feedback_language import feedback_summary, coaching_matches_language

with patch.dict(os.environ, {"JWT_SECRET": "test-only-secret-with-at-least-32-characters"}):
    from app.services import gemini_feedback as coaching


class FeedbackLanguageTests(unittest.TestCase):
    def test_hindi_summary_for_every_score_and_silence(self):
        for prediction, score in [("", 0), ("नमस्ते", 95), ("नम", 60), ("म", 20)]:
            analysis = {"prediction": prediction, "accuracy_score": score,
                        "is_correct": score >= 80, "feedback": "English summary"}
            self.assertTrue(coaching_matches_language(feedback_summary(analysis, "hi"), "hi"))
            self.assertEqual(feedback_summary(analysis, "en"), "English summary")

    def test_mixed_or_empty_coaching_is_not_sent_to_hindi_voice(self):
        for text in ["", "Keep practising", "विश्लेषण: Good attempt", "Aap achha bole"]:
            self.assertFalse(coaching_matches_language(text, "hi"))
        self.assertTrue(coaching_matches_language("विश्लेषण: अच्छा प्रयास। जीभ को सहज रखें।", "hi"))

    def test_complete_long_guidance_is_not_truncated(self):
        text = "जीभ को सहज रखें। " * 80
        self.assertGreater(len(text.split()), 110)
        self.assertTrue(coaching_matches_language(text, "hi"))


class ProviderLanguageTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_mixed_and_truncated_responses_then_preserves_complete_text(self):
        complete = "विश्लेषण: अच्छा प्रयास।\n\nजीभ और मुख की स्थिति: जीभ को सहज रखें।\n\nअभ्यास सुझाव: धीरे बोलें। " * 12
        def response(text, reason):
            result = MagicMock(status_code=200)
            result.json.return_value = {"candidates": [{"finishReason": reason, "content": {"parts": [{"text": text}]}}]}
            return result
        client = AsyncMock()
        client.post.side_effect = [response("विश्लेषण: Good attempt", "STOP"), response("अधूरा निर्देश", "MAX_TOKENS"), response(complete, "STOP")]
        with patch.object(coaching.settings, "SWAR_GOOGLE_KEY", "test-key"), patch.object(coaching.settings, "GROQ_API_KEY", ""), patch.object(coaching.httpx, "AsyncClient") as factory:
            factory.return_value.__aenter__.return_value = client
            result = await coaching.generate_pronunciation_feedback("नमस्ते", "नम", 60, .4)
        self.assertEqual(result, complete.strip())
        self.assertEqual(client.post.await_count, 3)

    async def test_offline_defaults_to_hindi(self):
        with patch.object(coaching.settings, "SWAR_GOOGLE_KEY", ""), patch.object(coaching.settings, "GROQ_API_KEY", ""):
            result = await coaching.generate_pronunciation_feedback("नमस्ते", "नम", 60, .4)
        self.assertTrue(coaching_matches_language(result, "hi"))
