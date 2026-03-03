import asyncio
import json
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from fastapi import HTTPException
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

    def test_authenticated_user_can_read_stored_data(self) -> None:
        """It proxies stored JSON rows through the backend route."""
        with patch(
            "src.api.routes.pages.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch(
            "src.api.routes.pages.storage_manager.load_json_data",
            return_value=[{"total": 10}],
        ):
            response = asyncio.run(
                pages_routes.serve_stored_data("chat-1", "question-1", "fixed-token")
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.body), [{"total": 10}])

    def test_storage_route_requires_session_cookie(self) -> None:
        """It rejects storage reads when the session cookie is missing."""
        with self.assertRaises(HTTPException) as context:
            asyncio.run(
                pages_routes.serve_stored_data("chat-1", "question-1", None)
            )

        self.assertEqual(context.exception.status_code, 401)

    def test_authenticated_user_can_read_stored_graph(self) -> None:
        """It proxies stored graph bytes through the backend route."""
        with patch(
            "src.api.routes.pages.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch(
            "src.api.routes.pages.storage_manager.load_graph_image",
            return_value=b"png-binary",
        ):
            response = asyncio.run(
                pages_routes.serve_stored_graph("chat-1", "question-1", "fixed-token")
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.media_type, "image/png")
        self.assertEqual(response.body, b"png-binary")
