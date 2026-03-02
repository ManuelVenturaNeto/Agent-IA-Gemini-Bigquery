import unittest

from pydantic import ValidationError

from src.api.models import ModelRequest


class ModelRequestValidationTests(unittest.TestCase):
    """Tests for API payload validation."""

    def test_rejects_path_traversal_like_chat_id(self) -> None:
        """It blocks chat identifiers that could be used as path segments."""
        with self.assertRaises(ValidationError):
            ModelRequest(
                email="user@example.com",
                question="How much did my travel expenses cost this month?",
                chat_id="../escape",
                question_id="question-1",
                response_types=["TEXT"],
                question_context="TRAVEL",
            )

    def test_rejects_path_traversal_like_question_id(self) -> None:
        """It blocks question identifiers that could be used as path segments."""
        with self.assertRaises(ValidationError):
            ModelRequest(
                email="user@example.com",
                question="How much did my travel expenses cost this month?",
                chat_id="chat-1",
                question_id="../../escape",
                response_types=["TEXT"],
                question_context="TRAVEL",
            )

    def test_defaults_to_text_and_sql_when_response_types_are_missing(self) -> None:
        """It defaults to TEXT and SQL when the request omits response modes."""
        request = ModelRequest(
            email="user@example.com",
            question="How much did my travel expenses cost this month?",
            chat_id="chat-1",
            question_id="question-1",
            question_context="TRAVEL",
        )

        self.assertEqual(request.response_types, ["TEXT", "SQL"])

    def test_accepts_legacy_response_type_alias(self) -> None:
        """It normalizes the deprecated single response_type field."""
        request = ModelRequest(
            email="user@example.com",
            question="How much did my travel expenses cost this month?",
            chat_id="chat-1",
            question_id="question-1",
            response_type="graphic",
            question_context="TRAVEL",
        )

        self.assertEqual(request.response_types, ["GRAPH"])

    def test_rejects_invalid_response_types(self) -> None:
        """It rejects any unsupported response mode."""
        with self.assertRaises(ValidationError):
            ModelRequest(
                email="user@example.com",
                question="How much did my travel expenses cost this month?",
                chat_id="chat-1",
                question_id="question-1",
                response_types=["TEXT", "CSV"],
                question_context="TRAVEL",
            )
