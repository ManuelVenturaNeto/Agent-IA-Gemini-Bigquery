import unittest
from unittest.mock import Mock
from src.agents.security_agent.agent import SecurityAgent
from src.agents.security_agent.tool_kit import DirectIdentifierLookupDetector
from src.agents.security_agent.tool_kit import SecurityCategory
from src.agents.security_agent.tool_kit import SecurityDecision


class DirectIdentifierLookupDetectorTests(unittest.TestCase):
    """Tests for the local direct identifier lookup detector."""

    def _build_detector(self) -> DirectIdentifierLookupDetector:
        """Create a detector instance used by the local-rule tests."""
        return DirectIdentifierLookupDetector()

    def test_blocks_user_id_lookup(self) -> None:
        """It blocks a direct lookup that uses a numeric user id."""
        detector = self._build_detector()

        decision = detector.detect(
            "Give me data from user with id = 20"
        )

        self.assertIsNotNone(decision)
        self.assertFalse(decision.is_safe)
        self.assertEqual(decision.category, SecurityCategory.DIRECT_IDENTIFIER_LOOKUP)

    def test_blocks_email_lookup(self) -> None:
        """It blocks a direct lookup that uses an email address."""
        detector = self._build_detector()

        decision = detector.detect(
            "Show customer with email foo@bar.com"
        )

        self.assertIsNotNone(decision)
        self.assertFalse(decision.is_safe)
        self.assertEqual(decision.category, SecurityCategory.DIRECT_IDENTIFIER_LOOKUP)

    def test_allows_analytical_question(self) -> None:
        """It ignores a normal analytical question."""
        detector = self._build_detector()

        decision = detector.detect(
            "How much did my travel expenses cost this month?"
        )

        self.assertIsNone(decision)

    def test_allows_aggregate_question(self) -> None:
        """It ignores an aggregate question without a direct record lookup."""
        detector = self._build_detector()

        decision = detector.detect("Count users created this week")

        self.assertIsNone(decision)


class SecurityAgentCheckSafetyTests(unittest.TestCase):
    """Tests for SecurityAgent.check_safety."""

    def _build_agent(self) -> SecurityAgent:
        """Create a lightweight security agent with mocked collaborators."""
        agent = SecurityAgent.__new__(SecurityAgent)
        agent._detector = DirectIdentifierLookupDetector()
        agent._toolkit = Mock()
        agent.log_info = Mock()
        return agent

    def test_local_rule_skips_llm(self) -> None:
        """It returns the local detector result without calling the LLM."""
        agent = self._build_agent()

        decision = agent.check_safety(
            question_text="Give me data from user with id = 20",
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
        )

        agent._toolkit.invoke.assert_not_called()
        self.assertFalse(decision.is_safe)
        self.assertEqual(decision.category, SecurityCategory.DIRECT_IDENTIFIER_LOOKUP)

    def test_llm_runs_when_local_rule_does_not_match(self) -> None:
        """It calls the LLM fallback when the local rule does not match."""
        agent = self._build_agent()
        agent._toolkit.invoke.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )

        decision = agent.check_safety(
            question_text="Count users created this week",
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
        )

        agent._toolkit.invoke.assert_called_once_with("Count users created this week")
        self.assertTrue(decision.is_safe)
        self.assertEqual(decision.category, SecurityCategory.SAFE)
