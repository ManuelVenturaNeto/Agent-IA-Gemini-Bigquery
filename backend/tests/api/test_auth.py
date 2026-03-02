import unittest
from fastapi import HTTPException
from src.api import auth as auth_module


class AuthServiceTests(unittest.TestCase):
    """Tests for the authentication service helpers."""

    def setUp(self) -> None:
        """Clear shared tokens before each test."""
        auth_module._active_tokens.clear()

    def test_login_user_returns_token_payload(self) -> None:
        """It returns a bearer token payload for valid credentials."""
        original_generator = auth_module.token_urlsafe
        auth_module.token_urlsafe = lambda _: "fixed-token"

        try:
            payload = auth_module.login_user("user@example.com", "demo_password")
        finally:
            auth_module.token_urlsafe = original_generator

        self.assertEqual(payload["access_token"], "fixed-token")
        self.assertEqual(payload["token_type"], "bearer")
        self.assertEqual(payload["email"], "user@example.com")
        self.assertTrue(payload["can_view_runtime_logs"])

    def test_login_user_rejects_invalid_credentials(self) -> None:
        """It raises an HTTP error when credentials are invalid."""
        with self.assertRaises(HTTPException) as context:
            auth_module.login_user("user@example.com", "wrong")

        self.assertEqual(context.exception.status_code, 401)

    def test_validate_token_returns_user_payload(self) -> None:
        """It returns the stored user when the bearer token is valid."""
        auth_module._active_tokens["fixed-token"] = {
            "email": "user@example.com",
            "can_view_runtime_logs": True,
        }

        user = auth_module.validate_token("Bearer fixed-token")

        self.assertEqual(user["email"], "user@example.com")
        self.assertTrue(user["can_view_runtime_logs"])

    def test_login_user_marks_non_privileged_email(self) -> None:
        """It allows login for other emails but disables runtime log access."""
        original_generator = auth_module.token_urlsafe
        auth_module.token_urlsafe = lambda _: "other-token"

        try:
            payload = auth_module.login_user(
                "another_user@example.net",
                "demo_password",
            )
        finally:
            auth_module.token_urlsafe = original_generator

        self.assertEqual(payload["email"], "another_user@example.net")
        self.assertFalse(payload["can_view_runtime_logs"])

    def test_validate_token_rejects_missing_header(self) -> None:
        """It raises an HTTP error when the authorization header is missing."""
        with self.assertRaises(HTTPException) as context:
            auth_module.validate_token(None)

        self.assertEqual(context.exception.status_code, 401)
