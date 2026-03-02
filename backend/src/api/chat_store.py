import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.infra.logging_utils import LoggedComponent


SAFE_STORAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def generate_hash_id() -> str:
    return secrets.token_hex(16)


class ChatStoreManager(LoggedComponent):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.base_dir = base_dir.resolve()
        self.project_root = self.base_dir.parent
        self.chat_messages_path = self.base_dir / "chat_messages.json"
        self.storage_dir = self.base_dir / "storage"
        self.storage_dir.mkdir(exist_ok=True)
        self.log_debug("Chat store manager initialized.")

    def _reconcile_legacy_root_chat_store(self) -> None:
        legacy_chat_path = self.project_root / "chat_messages.json"
        if legacy_chat_path == self.chat_messages_path or not legacy_chat_path.exists():
            return

        if not self.chat_messages_path.exists():
            legacy_chat_path.replace(self.chat_messages_path)
            self.log_warning(
                f"Moved legacy chat store to {self.chat_messages_path}."
            )
            return

        legacy_chat_path.unlink(missing_ok=True)
        self.log_warning(
            "Removed legacy root-level chat_messages.json file."
        )

    def ensure_chat_store(self) -> None:
        self._reconcile_legacy_root_chat_store()

        if self.chat_messages_path.exists():
            return

        self.chat_messages_path.write_text(
            json.dumps(
                {
                    "chat_id": generate_hash_id(),
                    "mensages": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.log_info("Created chat_messages.json store.")

    def load_chat_store(self) -> dict[str, Any]:
        self.ensure_chat_store()

        try:
            payload = json.loads(self.chat_messages_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.log_warning("Invalid chat store JSON detected. Resetting store.")
            payload = {}

        chat_id = payload.get("chat_id")
        if not isinstance(chat_id, str) or not chat_id.strip():
            chat_id = generate_hash_id()
        elif SAFE_STORAGE_ID_PATTERN.fullmatch(chat_id.strip()) is None:
            chat_id = generate_hash_id()

        raw_messages = payload.get("mensages")
        messages: list[dict[str, str]] = []
        if isinstance(raw_messages, list):
            for item in raw_messages:
                if not isinstance(item, dict):
                    continue

                question = str(item.get("question") or "").strip()
                if not question:
                    continue

                messages.append(
                    {
                        "mensage_id": str(item.get("mensage_id") or generate_hash_id()),
                        "question": question,
                        "response": str(item.get("response") or ""),
                        "query": str(item.get("query") or ""),
                        "data_path": str(item.get("data_path") or ""),
                        "graph_path": str(item.get("graph_path") or ""),
                        "selected_graph_pattern": str(
                            item.get("selected_graph_pattern") or ""
                        ),
                        "response_types": self._normalize_response_types(
                            item.get("response_types")
                        ),
                        "graph_suggestions": self._normalize_graph_suggestions(
                            item.get("graph_suggestions")
                        ),
                        "created_at": str(item.get("created_at") or ""),
                    }
                )

        store = {
            "chat_id": chat_id,
            "mensages": messages,
        }
        self.chat_messages_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        self.log_debug(
            f"Chat store loaded. Messages: {len(messages)}.",
            chat_id=chat_id,
        )
        return store

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
        clean_question = question.strip()
        if not clean_question:
            self.log_warning(
                "Skipped empty question while updating chat store.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return

        store = self.load_chat_store()
        normalized_chat_id = chat_id.strip() or str(store["chat_id"])
        normalized_message_id = message_id.strip() or generate_hash_id()
        timestamp = datetime.now(timezone.utc).isoformat()
        clean_response = response.strip()
        clean_query = query.strip()
        clean_data_path = data_path.strip()
        clean_graph_path = graph_path.strip()
        clean_selected_graph_pattern = selected_graph_pattern.strip()
        normalized_response_types = self._normalize_response_types(response_types)
        normalized_graph_suggestions = self._normalize_graph_suggestions(
            graph_suggestions
        )

        store["chat_id"] = normalized_chat_id

        for item in store["mensages"]:
            if str(item.get("mensage_id")) != normalized_message_id:
                continue

            item["question"] = clean_question
            item["response"] = clean_response or str(item.get("response") or "")
            item["query"] = clean_query or str(item.get("query") or "")
            item["data_path"] = clean_data_path or str(item.get("data_path") or "")
            item["graph_path"] = clean_graph_path or str(item.get("graph_path") or "")
            item["selected_graph_pattern"] = (
                clean_selected_graph_pattern
                or str(item.get("selected_graph_pattern") or "")
            )
            item["response_types"] = (
                normalized_response_types
                or self._normalize_response_types(item.get("response_types"))
            )
            item["graph_suggestions"] = (
                normalized_graph_suggestions
                or self._normalize_graph_suggestions(item.get("graph_suggestions"))
            )
            item["created_at"] = str(item.get("created_at") or timestamp)
            self.chat_messages_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
            self.log_info(
                "Chat message updated in store.",
                user_email=user_email,
                chat_id=normalized_chat_id,
                question_id=normalized_message_id,
            )
            return

        store["mensages"].append(
            {
                "mensage_id": normalized_message_id,
                "question": clean_question,
                "response": clean_response,
                "query": clean_query,
                "data_path": clean_data_path,
                "graph_path": clean_graph_path,
                "selected_graph_pattern": clean_selected_graph_pattern,
                "response_types": normalized_response_types,
                "graph_suggestions": normalized_graph_suggestions,
                "created_at": timestamp,
            }
        )
        self.chat_messages_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        self.log_info(
            "Chat message created in store.",
            user_email=user_email,
            chat_id=normalized_chat_id,
            question_id=normalized_message_id,
        )

    def save_message_data(
        self,
        chat_id: str,
        message_id: str,
        response_data: object,
        user_email: str | None = None,
    ) -> str:
        if not isinstance(response_data, list):
            self.log_debug(
                "No structured response data to persist.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return ""

        message_storage_dir = self.storage_dir / chat_id / message_id
        message_storage_dir.mkdir(parents=True, exist_ok=True)
        data_file = message_storage_dir / "response_data.json"
        data_file.write_text(json.dumps(response_data, indent=2), encoding="utf-8")

        relative_path = f"/storage/{chat_id}/{message_id}/{data_file.name}"
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
        data_file = self.storage_dir / chat_id / message_id / "response_data.json"
        if not data_file.exists():
            self.log_warning(
                "Structured response data file was not found.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return None

        try:
            payload = json.loads(data_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.log_warning(
                "Invalid structured response data JSON detected.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return None

        if not isinstance(payload, list):
            self.log_warning(
                "Structured response data is not a list.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=message_id,
            )
            return None

        return [item for item in payload if isinstance(item, dict)]

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
        """Update non-question metadata for an existing message."""
        store = self.load_chat_store()
        normalized_message_id = message_id.strip()
        normalized_response_types = self._normalize_response_types(response_types)
        normalized_graph_suggestions = self._normalize_graph_suggestions(
            graph_suggestions
        )

        for item in store["mensages"]:
            if str(item.get("mensage_id")) != normalized_message_id:
                continue

            if data_path is not None:
                item["data_path"] = data_path.strip()
            if graph_path is not None:
                item["graph_path"] = graph_path.strip()
            if selected_graph_pattern is not None:
                item["selected_graph_pattern"] = selected_graph_pattern.strip()
            if response_types is not None:
                item["response_types"] = normalized_response_types
            if graph_suggestions is not None:
                item["graph_suggestions"] = normalized_graph_suggestions

            self.chat_messages_path.write_text(
                json.dumps(store, indent=2),
                encoding="utf-8",
            )
            self.log_info(
                "Chat message metadata updated in store.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=normalized_message_id,
            )
            return True

        self.log_warning(
            "Chat message metadata update skipped because the message was not found.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=normalized_message_id,
        )
        return False

    def _normalize_response_types(self, response_types: object) -> list[str]:
        """Normalize stored response types into a simple list of strings."""
        if not isinstance(response_types, list):
            return []

        normalized_values: list[str] = []
        seen_values: set[str] = set()
        for value in response_types:
            text_value = str(value or "").strip().upper()
            if not text_value or text_value in seen_values:
                continue

            normalized_values.append(text_value)
            seen_values.add(text_value)

        return normalized_values

    def _normalize_graph_suggestions(
        self,
        graph_suggestions: object,
    ) -> list[dict[str, str]]:
        """Normalize stored graph suggestion payloads into serializable dicts."""
        if not isinstance(graph_suggestions, list):
            return []

        normalized_suggestions: list[dict[str, str]] = []
        for item in graph_suggestions:
            if not isinstance(item, dict):
                continue

            suggestion = {
                "id": str(item.get("id") or ""),
                "label": str(item.get("label") or ""),
                "reason": str(item.get("reason") or ""),
                "x_field": str(item.get("x_field") or ""),
                "y_field": str(item.get("y_field") or ""),
                "hue_field": str(item.get("hue_field") or ""),
            }
            if not suggestion["id"]:
                continue

            normalized_suggestions.append(suggestion)

        return normalized_suggestions
