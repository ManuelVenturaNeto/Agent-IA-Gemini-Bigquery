import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.api.chat_store import ChatStoreManager


class ChatStoreManagerTests(unittest.TestCase):
    """Tests for chat store persistence safeguards."""

    def test_load_chat_store_replaces_unsafe_chat_id(self) -> None:
        """It rewrites legacy path-like chat ids to a safe generated identifier."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            chat_store_path = base_dir / "chat_messages.json"
            chat_store_path.write_text(
                '{"chat_id":"../escape","mensages":[]}',
                encoding="utf-8",
            )

            manager = ChatStoreManager(base_dir)
            manager.log_debug = Mock()
            manager.log_info = Mock()
            manager.log_warning = Mock()

            store = manager.load_chat_store()

        self.assertNotEqual(store["chat_id"], "../escape")
        self.assertRegex(store["chat_id"], r"^[a-f0-9]{32}$")

    def test_updates_existing_message_metadata(self) -> None:
        """It updates graph-related metadata without rewriting the original question."""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = ChatStoreManager(Path(temp_dir))
            manager.log_debug = Mock()
            manager.log_info = Mock()
            manager.log_warning = Mock()

            manager.upsert_mock_message(
                "chat-1",
                "question-1",
                "Show expenses",
                response_types=["TEXT", "SQL"],
            )
            updated = manager.update_message_metadata(
                "chat-1",
                "question-1",
                graph_path="/storage/chat-1/graphics/question-1/graph.png",
                selected_graph_pattern="bar_vertical",
                graph_suggestions=[
                    {
                        "id": "bar_vertical",
                        "label": "Bar",
                        "reason": "Compares categories.",
                        "x_field": "month",
                        "y_field": "total",
                        "hue_field": "",
                    }
                ],
            )
            store = manager.load_chat_store()

        self.assertTrue(updated)
        self.assertEqual(store["mensages"][0]["graph_path"], "/storage/chat-1/graphics/question-1/graph.png")
        self.assertEqual(store["mensages"][0]["selected_graph_pattern"], "bar_vertical")
        self.assertEqual(store["mensages"][0]["response_types"], ["TEXT", "SQL"])
