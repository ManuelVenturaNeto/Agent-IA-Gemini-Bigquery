import unittest
from unittest.mock import Mock
from unittest.mock import patch
from src.agents.response_agent.agent import ResponseAgent


class ResponseAgentGenerateNaturalLanguageTests(unittest.TestCase):
    """Tests for ResponseAgent.generate_natural_language."""

    def _build_agent(self) -> ResponseAgent:
        """Create a response agent instance without running the real constructor."""
        agent = ResponseAgent.__new__(ResponseAgent)
        agent._chain = Mock()
        agent.log_info = Mock()
        agent.log_warning = Mock()
        return agent

    def test_returns_fallback_when_no_rows_are_found(self) -> None:
        """It returns the fixed fallback message when no data is returned."""
        agent = self._build_agent()

        response = agent.generate_natural_language(
            question_text="Show my flights",
            response_data=[],
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
        )

        self.assertEqual(
            response,
            "Nao encontrei registros para a sua solicitacao no banco de dados.",
        )
        agent._chain.invoke.assert_not_called()
        agent.log_warning.assert_called_once()

    def test_returns_llm_response_when_rows_exist(self) -> None:
        """It uses chat history and returns the LLM response when data exists."""
        agent = self._build_agent()
        history = Mock()
        history.messages = []
        agent._chain.invoke.return_value = "formatted answer"

        with patch(
            "src.agents.response_agent.agent.get_session_history",
            return_value=history,
        ):
            response = agent.generate_natural_language(
                question_text="Show my flights",
                response_data=[{"id_empresa": 1}],
                user_email="user@example.com",
                chat_id="chat-1",
                question_id="question-1",
            )

        self.assertEqual(response, "formatted answer")
        agent._chain.invoke.assert_called_once()
        history.add_user_message.assert_called_once_with("Show my flights")
        history.add_ai_message.assert_called_once_with("formatted answer")
        agent.log_info.assert_called_once()
