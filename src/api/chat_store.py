import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.infra.logging_utils import LoggedComponent


def generate_hash_id() -> str:
    return secrets.token_hex(16)


class ChatStoreManager(LoggedComponent):
    def __init__(self, base_dir: Path) -> None:
        super().__init__()
        self.chat_messages_path = base_dir / "chat_mensages.json"
        self.storage_dir = base_dir / "storage"
        self.storage_dir.mkdir(exist_ok=True)
        self.log_debug("Chat store manager initialized.")

    def ensure_chat_store(self) -> None:
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
        self.log_info("Created chat_mensages.json store.")

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

        store["chat_id"] = normalized_chat_id

        for item in store["mensages"]:
            if str(item.get("mensage_id")) != normalized_message_id:
                continue

            item["question"] = clean_question
            item["response"] = clean_response or str(item.get("response") or "")
            item["query"] = clean_query or str(item.get("query") or "")
            item["data_path"] = clean_data_path or str(item.get("data_path") or "")
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
