import asyncio
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from src.api.routes import pages as pages_routes


class PagesRoutesTests(unittest.TestCase):
    """Tests for the hidden frontend helper routes."""

    def test_privileged_user_can_read_runtime_logs(self) -> None:
        """It returns the latest runtime logs for privileged authenticated users."""
        mock_log_path = Mock()
        mock_log_path.exists.return_value = True
        mock_log_path.read_text.return_value = (
            "line 1\n"
            "GET /v1/runtime-logs HTTP/1.1\n"
            "Serving runtime logs panel.\n"
            "line 2"
        )

        with patch(
            "src.api.routes.pages.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch(
            "src.api.routes.pages.pipeline_log_path",
            mock_log_path,
        ):
            response = asyncio.run(
                pages_routes.serve_runtime_logs("Bearer fixed-token")
            )

        self.assertTrue(response["can_view_runtime_logs"])
        self.assertEqual(response["logs"], "line 1\nline 2")

    def test_non_privileged_user_cannot_read_runtime_logs(self) -> None:
        """It hides runtime logs for authenticated users outside the allow list."""
        with patch(
            "src.api.routes.pages.validate_token",
            return_value={
                "email": "another_user@example.net",
                "can_view_runtime_logs": False,
            },
        ):
            response = asyncio.run(
                pages_routes.serve_runtime_logs("Bearer fixed-token")
            )

        self.assertFalse(response["can_view_runtime_logs"])
        self.assertEqual(response["logs"], "")
