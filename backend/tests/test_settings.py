import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.infra.config.settings import BackendSettings


class BackendSettingsTests(unittest.TestCase):
    """Tests for centralized backend environment loading."""

    def test_loads_values_from_custom_env_file(self) -> None:
        """It reads settings from a provided .env path and resolves relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "APP_PORT=9001",
                        "PROJECT_ID=test-project",
                        "PROJECT_SA=service-account.json",
                        (
                            "PRIVILEGED_LOG_VIEWER_EMAILS="
                            "one@example.com,two@example.com"
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                custom_settings = BackendSettings(env_path=env_path, override=True)

                self.assertEqual(custom_settings.app_port, 9001)
                self.assertEqual(custom_settings.project_id, "test-project")
                self.assertEqual(
                    custom_settings.project_sa_path,
                    str((Path(temp_dir) / "service-account.json").resolve()),
                )
                self.assertEqual(
                    custom_settings.privileged_log_viewer_emails,
                    {"one@example.com", "two@example.com"},
                )
