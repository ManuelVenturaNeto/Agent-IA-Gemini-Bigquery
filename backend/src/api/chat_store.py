import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.api.chat_store_schema import ChatStore
from src.api.chat_store_schema import ChatStoreSerializer
from src.api.chat_store_schema import clean_text
from src.api.chat_store_schema import generate_hash_id
from src.api.chat_store_schema import STORE_CHAT_ID_KEY
from src.api.chat_store_schema import STORE_MESSAGES_KEY
from src.infra.config.config_google.storage_manager import StorageManager
from src.infra.logging_utils import LoggedComponent


class ChatStoreManager(LoggedComponent):
    """Manage local chat metadata and delegate structured payload storage."""

    def __init__(self, base_dir: Path, storage_manager: StorageManager) -> None:
        super().__init__()
        self.base_dir = base_dir.resolve()
        self.project_root = self.base_dir.parent
        self.chat_messages_path = self.base_dir / "chat_messages.json"
        self.storage_manager = storage_manager
        self.serializer = ChatStoreSerializer()
        self.log_debug("Chat store manager initialized.")

    def _reconcile_legacy_root_chat_store(self) -> None:
        legacy_chat_path = self.project_root / "chat_messages.json"
        if legacy_chat_path == self.chat_messages_path or not legacy_chat_path.exists():
            return

        if not self.chat_messages_path.exists():
            legacy_chat_path.replace(self.chat_messages_path)
            self.log_warning(f"Moved legacy chat store to {self.chat_messages_path}.")
            return

        legacy_chat_path.unlink(missing_ok=True)
        self.log_warning("Removed legacy root-level chat_messages.json file.")

    def ensure_chat_store(self) -> None:
        """Ensure the canonical chat store file exists."""
        self._reconcile_legacy_root_chat_store()
        if self.chat_messages_path.exists():
            return

        self._write_store(self.serializer.build_default_store())
        self.log_info("Created chat_messages.json store.")

    def load_chat_store(self) -> ChatStore:
        """Load, normalize, and persist the canonical chat store structure."""
        self.ensure_chat_store()
        payload = self._read_store_payload()
        store = self.serializer.normalize_store(payload)
        self._write_store(store)

        self.log_debug(
            f"Chat store loaded. Messages: {len(store[STORE_MESSAGES_KEY])}.",
            chat_id=store[STORE_CHAT_ID_KEY],
        )
        return store

    def upsert_message(
        self,
        chat_id: str,
        message_id: str,
        question: str,
        response: str = "",
        query: str = "",
        data_path: str = "",
        graph_path: str = "",
        selected_graph_pattern: str = "",
        response_types: list[str] | None = None,
        graph_suggestions: list[dict[str, str]] | None = None,
        user_email: str | None = None,
    ) -> None:
        """Create or update a message while preserving existing non-empty metadata."""
        clean_question = clean_text(question)
        if not clean_question:
            self.log_warning(
                "Skipped empty question while updating chat store.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return

        store = self.load_chat_store()
        normalized_chat_id = clean_text(chat_id) or str(store[STORE_CHAT_ID_KEY])
        normalized_message_id = clean_text(message_id) or generate_hash_id()
        timestamp = self._current_timestamp()

        incoming_message = self.serializer.build_message_record(
            message_id=normalized_message_id,
            question=clean_question,
            response=clean_text(response),
            query=clean_text(query),
            data_path=clean_text(data_path),
            graph_path=clean_text(graph_path),
            selected_graph_pattern=clean_text(selected_graph_pattern),
            response_types=self.serializer.normalize_response_types(response_types),
            graph_suggestions=self.serializer.normalize_graph_suggestions(
                graph_suggestions
            ),
            created_at=timestamp,
        )

        store[STORE_CHAT_ID_KEY] = normalized_chat_id
        existing_message = self.serializer.find_message(store, normalized_message_id)

        if existing_message is None:
            store[STORE_MESSAGES_KEY].append(incoming_message)
            action_message = "Chat message created in store."
        else:
            self.serializer.merge_upsert(existing_message, incoming_message, timestamp)
            action_message = "Chat message updated in store."

        self._write_store(store)
        self.log_info(
            action_message,
            user_email=user_email,
            chat_id=normalized_chat_id,
            question_id=normalized_message_id,
        )

    def upsert_mock_message(
        self,
        chat_id: str,
        message_id: str,
        question: str,
        response: str = "",
        query: str = "",
        data_path: str = "",
        graph_path: str = "",
        selected_graph_pattern: str = "",
        response_types: list[str] | None = None,
        graph_suggestions: list[dict[str, str]] | None = None,
        user_email: str | None = None,
    ) -> None:
        """Backward-compatible alias for the message upsert operation."""
        self.upsert_message(
            chat_id=chat_id,
            message_id=message_id,
            question=question,
            response=response,
            query=query,
            data_path=data_path,
            graph_path=graph_path,
            selected_graph_pattern=selected_graph_pattern,
            response_types=response_types,
            graph_suggestions=graph_suggestions,
            user_email=user_email,
        )

    def save_message_data(
        self,
        chat_id: str,
        message_id: str,
        response_data: object,
        user_email: str | None = None,
    ) -> str:
        """Persist structured query rows in cloud storage and return the access path."""
        if not isinstance(response_data, list):
            self.log_debug(
                "No structured response data to persist.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return ""

        if not user_email:
            self.log_warning(
                "Structured response data was not stored because the user email is missing.",
                chat_id=chat_id,
                question_id=message_id,
            )
            return ""

        payload = [item for item in response_data if isinstance(item, dict)]
        relative_path = self.storage_manager.save_json_data(
            user_email=user_email,
            chat_id=chat_id,
            message_id=message_id,
            payload=payload,
        )
        self.log_info(
            f"Response data stored at {relative_path}.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=message_id,
        )
        return relative_path

    def load_message_data(
        self,
        chat_id: str,
        message_id: str,
        user_email: str | None = None,
    ) -> list[dict[str, Any]] | None:
        """Load the persisted structured response rows for a given message."""
        if not user_email:
            self.log_warning(
                "Structured response data could not be loaded because the user email is missing.",
                chat_id=chat_id,
                question_id=message_id,
            )
            return None

        payload = self.storage_manager.load_json_data(
            user_email=user_email,
            chat_id=chat_id,
            message_id=message_id,
        )
        if payload is None:
            self.log_warning(
                "Structured response data file was not found.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return None

        return payload

    def update_message_metadata(
        self,
        chat_id: str,
        message_id: str,
        *,
        data_path: str | None = None,
        graph_path: str | None = None,
        selected_graph_pattern: str | None = None,
        response_types: list[str] | None = None,
        graph_suggestions: list[dict[str, str]] | None = None,
        user_email: str | None = None,
    ) -> bool:
        """Update stored metadata fields for an existing message."""
        store = self.load_chat_store()
        normalized_message_id = clean_text(message_id)
        existing_message = self.serializer.find_message(store, normalized_message_id)

        if existing_message is None:
            self.log_warning(
                "Chat message metadata update skipped because the message was not found.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=normalized_message_id,
            )
            return False

        if data_path is not None:
            existing_message["data_path"] = clean_text(data_path)
        if graph_path is not None:
            existing_message["graph_path"] = clean_text(graph_path)
        if selected_graph_pattern is not None:
            existing_message["selected_graph_pattern"] = clean_text(
                selected_graph_pattern
            )
        if response_types is not None:
            existing_message["response_types"] = self.serializer.normalize_response_types(
                response_types
            )
        if graph_suggestions is not None:
            existing_message[
                "graph_suggestions"
            ] = self.serializer.normalize_graph_suggestions(graph_suggestions)

        self._write_store(store)
        self.log_info(
            "Chat message metadata updated in store.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=normalized_message_id,
        )
        return True

    def _read_store_payload(self) -> ChatStore:
        try:
            return json.loads(self.chat_messages_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.log_warning("Invalid chat store JSON detected. Resetting store.")
            return {}

    def _write_store(self, store: ChatStore) -> None:
        self.chat_messages_path.write_text(
            json.dumps(store, indent=2),
            encoding="utf-8",
        )

    def _current_timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
