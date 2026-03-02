import unittest
from src.api.app import app


class AppModuleTests(unittest.TestCase):
    """Tests for the FastAPI application setup."""

    def test_app_metadata_is_configured(self) -> None:
        """It exposes the expected API metadata."""
        self.assertEqual(app.title, "Analytical Agent Backend API")
        self.assertEqual(app.version, "1.0.0")

    def test_app_registers_core_routes(self) -> None:
        """It mounts the expected static paths and API endpoints."""
        paths = {route.path for route in app.routes}

        self.assertIn("/assets", paths)
        self.assertIn("/storage", paths)
        self.assertIn("/v1/login", paths)
        self.assertIn("/v1/session", paths)
        self.assertIn("/v1/ask", paths)
        self.assertIn("/v1/graph", paths)
        self.assertIn("/v1/runtime-logs", paths)
