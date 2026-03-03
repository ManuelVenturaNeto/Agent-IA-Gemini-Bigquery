import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = BACKEND_ROOT / ".env"


class BackendSettings:
    """Central access point for backend environment settings."""

    def __init__(
        self,
        env_path: Path | None = None,
        *,
        override: bool = False,
    ) -> None:
        self.env_path = Path(env_path or ENV_PATH)
        self.backend_root = self.env_path.parent
        load_dotenv(self.env_path, override=override)

    def _read_first(self, *keys: str, default: str = "") -> str:
        """Return the first non-empty environment value for the provided keys."""
        for key in keys:
            value = os.getenv(key, "").strip()
            if value:
                return value

        return default

    @property
    def app_host(self) -> str:
        return self._read_first("APP_HOST", default="127.0.0.1")

    @property
    def app_login_password(self) -> str:
        return self._read_first("APP_LOGIN_PASSWORD", default="demo_password")

    @property
    def app_port(self) -> int:
        raw_value = self._read_first("APP_PORT", default="8000")
        try:
            return int(raw_value)
        except ValueError as exp:
            raise ValueError("APP_PORT must be a valid integer.") from exp

    @property
    def gemini_api_key(self) -> str:
        return self._read_first(
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "GEN_IA_KEY",
        )

    @property
    def privileged_log_viewer_emails(self) -> set[str]:
        raw_value = self._read_first(
            "PRIVILEGED_LOG_VIEWER_EMAILS",
            default="user@example.com",
        )
        return {
            item.strip().lower()
            for item in raw_value.split(",")
            if item.strip()
        }

    @property
    def project_id(self) -> str:
        return self._read_first(
            "PROJECT_ID",
            "PROJECT",
            "GOOGLE_CLOUD_PROJECT",
            "GCP_PROJECT_ID",
        )

    @property
    def project_sa_path(self) -> str:
        raw_value = self._read_first("PROJECT_SA")
        if not raw_value:
            return ""

        candidate_path = Path(raw_value)
        if candidate_path.is_absolute():
            return str(candidate_path)

        return str((self.backend_root / candidate_path).resolve())

    def storage_bucket(self, default_bucket: str) -> str:
        return self._read_first("STORAGE_BUCKET", default=default_bucket)


settings = BackendSettings()
