import re
import secrets
from typing import Any


SAFE_STORAGE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

STORE_CHAT_ID_KEY = "chat_id"
STORE_MESSAGES_KEY = "mensages"  # Legacy persisted key kept for compatibility.
MESSAGE_ID_KEY = "mensage_id"  # Legacy persisted key kept for compatibility.

GRAPH_SUGGESTION_FIELDS = (
    "id",
    "label",
    "reason",
    "x_field",
    "y_field",
    "hue_field",
)

ChatStore = dict[str, Any]
ChatMessage = dict[str, Any]
GraphSuggestion = dict[str, str]


def generate_hash_id() -> str:
    return secrets.token_hex(16)


def as_text(value: object) -> str:
    return str(value or "")


def clean_text(value: object) -> str:
    return as_text(value).strip()


class ChatStoreSerializer:
    """Own the persisted chat-store schema and normalization rules."""

    def build_default_store(self) -> ChatStore:
        return {
            STORE_CHAT_ID_KEY: generate_hash_id(),
            STORE_MESSAGES_KEY: [],
        }

    def normalize_store(self, payload: object) -> ChatStore:
        raw_payload = payload if isinstance(payload, dict) else {}
        return {
            STORE_CHAT_ID_KEY: self._normalize_chat_id(
                raw_payload.get(STORE_CHAT_ID_KEY)
            ),
            STORE_MESSAGES_KEY: self._normalize_messages(
                raw_payload.get(STORE_MESSAGES_KEY)
            ),
        }

    def build_message_record(
        self,
        *,
        message_id: str,
        question: str,
        response: str,
        query: str,
        data_path: str,
        graph_path: str,
        selected_graph_pattern: str,
        response_types: list[str],
        graph_suggestions: list[GraphSuggestion],
        created_at: str,
    ) -> ChatMessage:
        return {
            MESSAGE_ID_KEY: message_id,
            "question": question,
            "response": response,
            "query": query,
            "data_path": data_path,
            "graph_path": graph_path,
            "selected_graph_pattern": selected_graph_pattern,
            "response_types": response_types,
            "graph_suggestions": graph_suggestions,
            "created_at": created_at,
        }

    def find_message(
        self,
        store: ChatStore,
        message_id: str,
    ) -> ChatMessage | None:
        for item in store[STORE_MESSAGES_KEY]:
            if str(item.get(MESSAGE_ID_KEY)) == message_id:
                return item

        return None

    def merge_upsert(
        self,
        existing_message: ChatMessage,
        incoming_message: ChatMessage,
        timestamp: str,
    ) -> None:
        existing_message["question"] = incoming_message["question"]
        for field in (
            "response",
            "query",
            "data_path",
            "graph_path",
            "selected_graph_pattern",
        ):
            existing_message[field] = self._prefer_non_empty(
                incoming_message[field],
                existing_message.get(field),
            )

        existing_message["response_types"] = (
            incoming_message["response_types"] or existing_message["response_types"]
        )
        existing_message["graph_suggestions"] = (
            incoming_message["graph_suggestions"]
            or existing_message["graph_suggestions"]
        )
        existing_message["created_at"] = (
            as_text(existing_message.get("created_at")) or timestamp
        )

    def normalize_response_types(self, response_types: object) -> list[str]:
        """Normalize stored response types into a simple list of strings."""
        if not isinstance(response_types, list):
            return []

        normalized_values: list[str] = []
        seen_values: set[str] = set()
        for value in response_types:
            text_value = clean_text(value).upper()
            if not text_value or text_value in seen_values:
                continue

            normalized_values.append(text_value)
            seen_values.add(text_value)

        return normalized_values

    def normalize_graph_suggestions(
        self,
        graph_suggestions: object,
    ) -> list[GraphSuggestion]:
        """Normalize stored graph suggestion payloads into serializable dicts."""
        if not isinstance(graph_suggestions, list):
            return []

        normalized_suggestions: list[GraphSuggestion] = []
        for item in graph_suggestions:
            if not isinstance(item, dict):
                continue

            suggestion = {
                field: as_text(item.get(field))
                for field in GRAPH_SUGGESTION_FIELDS
            }
            if not suggestion["id"]:
                continue

            normalized_suggestions.append(suggestion)

        return normalized_suggestions

    def _normalize_chat_id(self, raw_chat_id: object) -> str:
        chat_id = clean_text(raw_chat_id)
        if not chat_id:
            return generate_hash_id()
        if SAFE_STORAGE_ID_PATTERN.fullmatch(chat_id) is None:
            return generate_hash_id()
        return chat_id

    def _normalize_messages(self, raw_messages: object) -> list[ChatMessage]:
        if not isinstance(raw_messages, list):
            return []

        normalized_messages: list[ChatMessage] = []
        for item in raw_messages:
            normalized_message = self._normalize_message(item)
            if normalized_message is not None:
                normalized_messages.append(normalized_message)

        return normalized_messages

    def _normalize_message(self, raw_message: object) -> ChatMessage | None:
        if not isinstance(raw_message, dict):
            return None

        question = clean_text(raw_message.get("question"))
        if not question:
            return None

        return self.build_message_record(
            message_id=as_text(raw_message.get(MESSAGE_ID_KEY)) or generate_hash_id(),
            question=question,
            response=as_text(raw_message.get("response")),
            query=as_text(raw_message.get("query")),
            data_path=as_text(raw_message.get("data_path")),
            graph_path=as_text(raw_message.get("graph_path")),
            selected_graph_pattern=as_text(raw_message.get("selected_graph_pattern")),
            response_types=self.normalize_response_types(
                raw_message.get("response_types")
            ),
            graph_suggestions=self.normalize_graph_suggestions(
                raw_message.get("graph_suggestions")
            ),
            created_at=as_text(raw_message.get("created_at")),
        )

    def _prefer_non_empty(self, new_value: object, current_value: object) -> str:
        normalized_new_value = clean_text(new_value)
        if normalized_new_value:
            return normalized_new_value

        return as_text(current_value)
