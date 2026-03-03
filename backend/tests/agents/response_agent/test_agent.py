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
        agent._chain.invoke.return_value = (
            "The report highlights the average, mode, outlier, and trend clearly."
        )

        with patch(
            "src.agents.response_agent.agent.get_session_history",
            return_value=history,
        ):
            response = agent.generate_natural_language(
                question_text="Show my flights",
                response_data=[{"company_id": 1}],
                user_email="user@example.com",
                chat_id="chat-1",
                question_id="question-1",
            )

        self.assertEqual(
            response,
            "The report highlights the average, mode, outlier, and trend clearly.",
        )
        agent._chain.invoke.assert_called_once()
        payload = agent._chain.invoke.call_args.args[0]
        self.assertEqual(payload["response_data"], '[{"company_id": 1}]')
        self.assertEqual(payload["history"], history.messages)
        self.assertEqual(payload["question_text"], "Show my flights")
        self.assertIn("Destaques analiticos", payload["analysis_summary"])
        history.add_user_message.assert_called_once_with("Show my flights")
        history.add_ai_message.assert_called_once_with(
            "The report highlights the average, mode, outlier, and trend clearly."
        )
        agent.log_info.assert_called_once()

    def test_replaces_raw_dump_with_paragraph_report(self) -> None:
        """It converts a dump-like LLM output into a readable paragraph report."""
        agent = self._build_agent()
        history = Mock()
        history.messages = []
        agent._chain.invoke.return_value = '[{"ticket": "AZ123", "price": 540}]'

        with patch(
            "src.agents.response_agent.agent.get_session_history",
            return_value=history,
        ):
            response = agent.generate_natural_language(
                question_text="Show my flights",
                response_data=[{"ticket": "AZ123", "price": 540}],
                user_email="user@example.com",
                chat_id="chat-1",
                question_id="question-1",
            )

        self.assertIn("Com base nos dados retornados", response)
        self.assertIn("\n\n", response)
        self.assertIn("Destaques analiticos", response)
        self.assertIn("media", response)
        self.assertIn("outlier", response)
        self.assertIn("tendencia", response)
        self.assertIn("ticket=AZ123", response)
        history.add_ai_message.assert_called_once_with(response)

    def test_appends_analytical_brief_when_model_response_is_too_generic(self) -> None:
        """It appends computed insights when the model omits analytical details."""
        agent = self._build_agent()
        history = Mock()
        history.messages = []
        agent._chain.invoke.return_value = "Resumo objetivo da consulta."

        with patch(
            "src.agents.response_agent.agent.get_session_history",
            return_value=history,
        ):
            response = agent.generate_natural_language(
                question_text="Show my sales trend",
                response_data=[
                    {"date": "2026-01-01", "amount": 10, "category": "A"},
                    {"date": "2026-01-02", "amount": 12, "category": "A"},
                    {"date": "2026-01-03", "amount": 14, "category": "B"},
                    {"date": "2026-01-04", "amount": 40, "category": "A"},
                ],
                user_email="user@example.com",
                chat_id="chat-1",
                question_id="question-1",
            )

        self.assertTrue(response.startswith("Resumo objetivo da consulta."))
        self.assertIn("Destaques analiticos", response)
        self.assertIn("media e", response)
        self.assertIn("moda", response)
        self.assertIn("outlier", response)
        self.assertIn("tendencia", response)
