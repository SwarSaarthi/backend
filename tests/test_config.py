import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

# Import application configuration without using any developer credentials.
TEST_SECRET = "test-only-signing-secret-with-at-least-32-characters"
with patch.dict(os.environ, {"JWT_SECRET": TEST_SECRET, "DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
    from app.config import Settings


class SigningSecretTests(unittest.TestCase):
    def test_missing_secret_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValidationError):
                Settings(_env_file=None)

    def test_empty_short_whitespace_and_previous_default_are_rejected(self):
        for secret in ("", "short", " " * 40, "swarsaarthi-super-secret-jwt-key-2026"):
            with self.subTest(secret_kind=len(secret)):
                with self.assertRaises(ValidationError):
                    Settings(_env_file=None, JWT_SECRET=secret)

    def test_configured_secret_is_preserved_and_not_printed(self):
        settings = Settings(_env_file=None, JWT_SECRET=TEST_SECRET)
        self.assertEqual(settings.JWT_SECRET, TEST_SECRET)
        self.assertNotIn(TEST_SECRET, repr(settings))


if __name__ == "__main__":
    unittest.main()
