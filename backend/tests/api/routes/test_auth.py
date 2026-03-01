import asyncio
import unittest
from unittest.mock import patch
from src.api.models import LoginRequest
from src.api.routes import auth as auth_routes


class AuthRoutesTests(unittest.TestCase):
    """Tests for the authentication API routes."""

    def test_login_returns_payload(self) -> None:
        """It returns the login payload from the auth service."""
        with patch(
            "src.api.routes.auth.login_user",
            return_value={
                "access_token": "fixed-token",
                "token_type": "bearer",
                "username": "demo_user",
                "email": "user@example.com",
            },
        ):
            response = asyncio.run(
                auth_routes.login(
                    LoginRequest(username="demo_user", password="demo_password")
                )
            )

        self.assertEqual(response["access_token"], "fixed-token")
        self.assertEqual(response["email"], "user@example.com")

    def test_session_status_returns_validated_user(self) -> None:
        """It returns the validated user payload from the auth service."""
        with patch(
            "src.api.routes.auth.validate_token",
            return_value={
                "username": "demo_user",
                "email": "user@example.com",
            },
        ):
            response = asyncio.run(auth_routes.session_status("Bearer fixed-token"))

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["username"], "demo_user")
