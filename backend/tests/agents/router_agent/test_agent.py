import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from src.agents.router_agent.agent import RouterAgent


class RouterAgentIdentifyContextTests(unittest.TestCase):
    """Tests for RouterAgent.identify_context."""

    def _build_agent(self) -> RouterAgent:
        """Create a router agent instance without running the real constructor."""
        agent = RouterAgent.__new__(RouterAgent)
        agent._chain = Mock()
        agent.log_info = Mock()
        return agent

    def test_returns_uppercase_context(self) -> None:
        """It normalizes the LLM result to uppercase."""
        agent = self._build_agent()
        agent._chain.invoke.return_value = SimpleNamespace(context=" travel ")

        context = agent.identify_context(
            question_text="Show my flights",
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
        )

        self.assertEqual(context, "TRAVEL")
        agent.log_info.assert_called_once()
