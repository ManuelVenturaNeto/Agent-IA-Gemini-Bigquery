import unittest
from unittest.mock import Mock
from src.agents.query_agent.agent import QueryAgent


class QueryAgentGenerateSqlTests(unittest.TestCase):
    """Tests for QueryAgent.generate_sql."""

    def _build_agent(self) -> QueryAgent:
        """Create a query agent instance without running the real constructor."""
        agent = QueryAgent.__new__(QueryAgent)
        agent._chain = Mock()
        agent._clean_sql = Mock(side_effect=lambda sql: sql.strip())
        agent.log_info = Mock()
        agent.log_warning = Mock()
        agent.log_error = Mock()
        return agent

    def test_returns_valid_sql_after_retry(self) -> None:
        """It retries once and returns the first valid SQL statement."""
        agent = self._build_agent()
        agent._chain.invoke.side_effect = [
            "SELECT * FROM test",
            "SELECT id_empresa FROM test",
        ]

        sql = agent.generate_sql(
            question_text="Show expenses",
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
            tables_and_schemas={"test": {"id_empresa": "INTEGER"}},
        )

        self.assertEqual(sql, "SELECT id_empresa FROM test")
        self.assertEqual(agent._chain.invoke.call_count, 2)
        agent.log_info.assert_called_once()

    def test_raises_after_three_invalid_attempts(self) -> None:
        """It raises an error after three invalid SQL generations."""
        agent = self._build_agent()
        agent._chain.invoke.side_effect = [
            "SELECT * FROM test",
            "SELECT total FROM test",
            "SELECT total FROM test LIMIT 1",
        ]

        with self.assertRaises(ValueError):
            agent.generate_sql(
                question_text="Show expenses",
                user_email="user@example.com",
                chat_id="chat-1",
                question_id="question-1",
                tables_and_schemas={"test": {"id_empresa": "INTEGER"}},
            )

        self.assertEqual(agent._chain.invoke.call_count, 3)
        agent.log_error.assert_called_once()
