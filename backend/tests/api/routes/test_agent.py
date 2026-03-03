import asyncio
import unittest
from unittest.mock import Mock
from unittest.mock import patch
from fastapi import HTTPException
from src.api.models import GraphRequest
from src.api.models import ModelRequest
from src.api.routes import agent as agent_routes


class AgentRoutesTests(unittest.TestCase):
    """Tests for the ask-agent API route."""

    def test_ask_agent_returns_success_payload(self) -> None:
        """It returns the assembled response payload for a successful request."""
        request = ModelRequest(
            email="user@example.com",
            question="How much did my travel expenses cost this month?",
            chat_id="chat-1",
            question_id="question-1",
            response_types=["TEXT", "SQL"],
            question_context="TRAVEL",
        )

        orchestrator = Mock()
        orchestrator.run_agent.return_value = {
            "status": "success",
            "response_data": [{"company_id": 1}],
            "response_sql": "SELECT company_id FROM test",
            "response_natural_language": "formatted answer",
            "response_types": ["TEXT", "SQL"],
            "graph_suggestions": [],
            "graph_path": "",
            "selected_graph_pattern": "",
        }

        with patch(
            "src.api.routes.agent.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch(
            "src.api.routes.agent.OrchestrateAgent",
            return_value=orchestrator,
        ), patch.object(
            agent_routes.chat_store_manager,
            "save_message_data",
            return_value="/v1/storage/data/chat-1/question-1",
        ), patch.object(
            agent_routes.chat_store_manager,
            "upsert_mock_message",
        ):
            response = asyncio.run(agent_routes.ask_agent(request, "Bearer fixed-token"))

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["user"], "user@example.com")
        self.assertEqual(
            response["response"]["data_path"],
            "/v1/storage/data/chat-1/question-1",
        )

    def test_ask_agent_returns_http_400_for_invalid_input(self) -> None:
        """It raises HTTP 400 when the orchestrator rejects an invalid input."""
        request = ModelRequest(
            email="user@example.com",
            question="test",
            chat_id="chat-1",
            question_id="question-1",
            response_types=["TEXT"],
            question_context="TRAVEL",
        )

        orchestrator = Mock()
        orchestrator.run_agent.return_value = {
            "status": "error",
            "message": "Invalid input. Ask a clear business-related question.",
        }

        with patch(
            "src.api.routes.agent.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch(
            "src.api.routes.agent.OrchestrateAgent",
            return_value=orchestrator,
        ), patch.object(
            agent_routes.chat_store_manager,
            "save_message_data",
        ) as save_message_data, patch.object(
            agent_routes.chat_store_manager,
            "upsert_mock_message",
        ):
            with self.assertRaises(HTTPException) as context:
                asyncio.run(agent_routes.ask_agent(request, "Bearer fixed-token"))

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            "Invalid input. Ask a clear business-related question.",
        )
        save_message_data.assert_not_called()

    def test_generate_graph_returns_graph_payload(self) -> None:
        """It renders a graph from saved data and returns the graph path."""
        request = GraphRequest(
            chat_id="chat-1",
            question_id="question-1",
            graph_pattern_id="bar_vertical",
        )

        with patch(
            "src.api.routes.agent.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch.object(
            agent_routes.chat_store_manager,
            "load_message_data",
            return_value=[{"month": "2026-01", "total": 10}],
        ), patch.object(
            agent_routes.graph_agent,
            "suggest_graphs",
            return_value=[
                {
                    "id": "bar_vertical",
                    "label": "Bar",
                    "reason": "Compares categories.",
                    "x_field": "month",
                    "y_field": "total",
                    "hue_field": "",
                }
            ],
        ), patch.object(
            agent_routes.graph_agent,
            "render_graph",
            return_value="/v1/storage/graph/chat-1/question-1",
        ), patch.object(
            agent_routes.chat_store_manager,
            "update_message_metadata",
            return_value=True,
        ):
            response = asyncio.run(
                agent_routes.generate_graph(request, "Bearer fixed-token")
            )

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["graph_path"],
            "/v1/storage/graph/chat-1/question-1",
        )

    def test_generate_graph_returns_http_400_when_saved_data_is_missing(self) -> None:
        """It rejects graph generation when the message data was not found."""
        request = GraphRequest(
            chat_id="chat-1",
            question_id="question-1",
            graph_pattern_id="bar_vertical",
        )

        with patch(
            "src.api.routes.agent.validate_token",
            return_value={
                "email": "user@example.com",
                "can_view_runtime_logs": True,
            },
        ), patch.object(
            agent_routes.chat_store_manager,
            "load_message_data",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as context:
                asyncio.run(agent_routes.generate_graph(request, "Bearer fixed-token"))

        self.assertEqual(context.exception.status_code, 400)
