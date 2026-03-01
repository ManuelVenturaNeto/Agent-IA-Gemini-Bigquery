import asyncio
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from src.api.models import ModelRequest
from src.api.routes import agent as agent_routes


class AgentRoutesTests(unittest.TestCase):
    """Tests for the ask-agent API route."""

    def test_ask_agent_returns_success_payload(self) -> None:
        """It returns the assembled response payload for a successful request."""
        request = ModelRequest(
            email="manuueelneto@gmail.com",
            question="How much did my travel expenses cost this month?",
            chat_id="chat-1",
            question_id="question-1",
            response_type="TEXT",
            question_context="TRAVEL",
        )

        orchestrator = Mock()
        orchestrator.run_agent.return_value = {
            "status": "success",
            "response_data": [{"id_empresa": 1}],
            "response_sql": "SELECT id_empresa FROM test",
            "response_natural_language": "formatted answer",
        }

        with patch(
            "src.api.routes.agent.validate_token",
            return_value={
                "username": "manuel",
                "email": "manuueelneto@gmail.com",
            },
        ), patch(
            "src.api.routes.agent.OrchestrateAgent",
            return_value=orchestrator,
        ), patch.object(
            agent_routes.chat_store_manager,
            "save_message_data",
            return_value="/storage/chat-1/question-1/response_data.json",
        ), patch.object(
            agent_routes.chat_store_manager,
            "upsert_mock_message",
        ):
            response = asyncio.run(agent_routes.ask_agent(request, "Bearer fixed-token"))

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["user"], "manuel")
        self.assertEqual(
            response["response"]["data_path"],
            "/storage/chat-1/question-1/response_data.json",
        )
