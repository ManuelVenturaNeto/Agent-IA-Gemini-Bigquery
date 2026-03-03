import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.infra.logging_utils import LoggedComponent

try:
    from google.cloud import storage
except ImportError:  # pragma: no cover - depends on installed extras
    storage = None


DEFAULT_STORAGE_BUCKET = "agent_analytical"
DATA_ENDPOINT_TEMPLATE = "/v1/storage/data/{chat_id}/{message_id}"
GRAPH_ENDPOINT_TEMPLATE = "/v1/storage/graph/{chat_id}/{message_id}"


class StorageManager(LoggedComponent):
    """Handle persisted response data and graphs in Google Cloud Storage."""

    def __init__(self, bucket_name: str = DEFAULT_STORAGE_BUCKET) -> None:
        self._env_path = self._resolve_env_path()
        load_dotenv(self._env_path)
        super().__init__()
        self.bucket_name = os.getenv("STORAGE_BUCKET", bucket_name).strip()
        self.project_id = self._resolve_project_id()
        self.project_sa = self._resolve_service_account_path()
        self._bucket = None
        self._configuration_error = ""

        if storage is None:
            self._configuration_error = (
                "google-cloud-storage is not installed in the active environment."
            )
            self.log_warning(
                f"{self._configuration_error} Cloud storage is unavailable."
            )
            return

        if not self.project_sa:
            self._configuration_error = (
                "PROJECT_SA is not configured for Google Cloud authentication."
            )
            self.log_warning(
                f"{self._configuration_error} Cloud storage is unavailable."
            )
            return

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.project_sa
        try:
            client = storage.Client(project=self.project_id or None)
            self._bucket = client.bucket(self.bucket_name)
        except Exception as exp:
            self._configuration_error = f"Unable to initialize the storage client: {exp}"
            self.log_error(self._configuration_error)
            return

        resolved_project = self.project_id or client.project or "auto-detected"
        self.project_id = resolved_project
        self.log_debug(
            f"Storage bucket configured: {self.bucket_name} (project: {resolved_project})."
        )

    def save_json_data(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
        payload: list[dict[str, Any]],
    ) -> str:
        """Persist structured rows as JSON and return the API access path."""
        blob = self._build_blob(
            self._build_data_blob_name(
                user_email=user_email,
                chat_id=chat_id,
                message_id=message_id,
            )
        )
        blob.upload_from_string(
            json.dumps(payload, indent=2),
            content_type="application/json",
        )
        return self.build_data_access_path(chat_id=chat_id, message_id=message_id)

    def load_json_data(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
    ) -> list[dict[str, Any]] | None:
        """Load structured rows from cloud storage."""
        blob = self._build_blob(
            self._build_data_blob_name(
                user_email=user_email,
                chat_id=chat_id,
                message_id=message_id,
            )
        )

        try:
            payload = json.loads(blob.download_as_text(encoding="utf-8"))
        except Exception:
            return None

        if not isinstance(payload, list):
            return None

        return [item for item in payload if isinstance(item, dict)]

    def save_graph_image(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
        image_bytes: bytes,
    ) -> str:
        """Persist a rendered PNG graph and return the API access path."""
        blob = self._build_blob(
            self._build_graph_blob_name(
                user_email=user_email,
                chat_id=chat_id,
                message_id=message_id,
            )
        )
        blob.upload_from_string(image_bytes, content_type="image/png")
        return self.build_graph_access_path(chat_id=chat_id, message_id=message_id)

    def load_graph_image(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
    ) -> bytes | None:
        """Load a rendered PNG graph from cloud storage."""
        blob = self._build_blob(
            self._build_graph_blob_name(
                user_email=user_email,
                chat_id=chat_id,
                message_id=message_id,
            )
        )

        try:
            return blob.download_as_bytes()
        except Exception:
            return None

    def build_data_access_path(self, *, chat_id: str, message_id: str) -> str:
        """Return the backend route that proxies stored JSON data."""
        return DATA_ENDPOINT_TEMPLATE.format(
            chat_id=self._normalize_segment(chat_id),
            message_id=self._normalize_segment(message_id),
        )

    def build_graph_access_path(self, *, chat_id: str, message_id: str) -> str:
        """Return the backend route that proxies stored graph content."""
        return GRAPH_ENDPOINT_TEMPLATE.format(
            chat_id=self._normalize_segment(chat_id),
            message_id=self._normalize_segment(message_id),
        )

    def _build_data_blob_name(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
    ) -> str:
        return (
            f"{self._normalize_email(user_email)}/"
            f"{self._normalize_segment(chat_id)}/"
            f"data/{self._normalize_segment(message_id)}.json"
        )

    def _build_graph_blob_name(
        self,
        *,
        user_email: str,
        chat_id: str,
        message_id: str,
    ) -> str:
        return (
            f"{self._normalize_email(user_email)}/"
            f"{self._normalize_segment(chat_id)}/"
            f"graph/{self._normalize_segment(message_id)}.png"
        )

    def _build_blob(self, blob_name: str):
        bucket = self._require_bucket()
        return bucket.blob(blob_name)

    def _require_bucket(self):
        if self._bucket is None:
            detail = self._configuration_error or "unknown configuration error."
            raise RuntimeError(f"Cloud storage is not configured: {detail}")

        return self._bucket

    def _resolve_project_id(self) -> str:
        """Read the configured GCP project id from common environment names."""
        candidate_keys = (
            "PROJECT_ID",
            "PROJECT",
            "GOOGLE_CLOUD_PROJECT",
            "GCP_PROJECT_ID",
        )

        for key in candidate_keys:
            value = os.getenv(key, "").strip()
            if value:
                return value

        return ""

    def _resolve_env_path(self) -> Path:
        """Return the backend .env path so loading does not depend on cwd."""
        return Path(__file__).resolve().parents[4] / ".env"

    def _resolve_service_account_path(self) -> str:
        """Return an absolute service-account path from PROJECT_SA."""
        raw_value = os.getenv("PROJECT_SA", "").strip()
        if not raw_value:
            return ""

        candidate_path = Path(raw_value)
        if candidate_path.is_absolute():
            return str(candidate_path)

        return str((self._env_path.parent / candidate_path).resolve())

    def _normalize_email(self, value: str) -> str:
        normalized = str(value or "").strip().lower().replace("/", "_")
        if not normalized:
            raise ValueError("A valid email is required for storage paths.")

        return normalized

    def _normalize_segment(self, value: str) -> str:
        normalized = str(value or "").strip().replace("/", "_")
        if not normalized:
            raise ValueError("Storage path segments cannot be empty.")

        return normalized
