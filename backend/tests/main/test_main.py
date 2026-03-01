import unittest
from unittest.mock import patch
from src.agents.security_agent.tool_kit import SecurityCategory
from src.agents.security_agent.tool_kit import SecurityDecision
from src.main.main import OrchestrateAgent


class OrchestrateAgentSecurityTests(unittest.TestCase):
    """Tests for orchestration behavior around the security gate."""

    def _build_orchestrator_with_mocks(self):
        """Create an orchestrator and expose its mocked collaborators."""
        patchers = {
            "security": patch("src.main.main.SecurityAgent"),
            "router": patch("src.main.main.RouterAgent"),
            "query": patch("src.main.main.QueryAgent"),
            "response": patch("src.main.main.ResponseAgent"),
            "db": patch("src.main.main.BigQueryManager"),
        }

        instances = {}

        for name, patcher in patchers.items():
            mocked_class = patcher.start()
            self.addCleanup(patcher.stop)
            instances[name] = mocked_class.return_value

        instances["db"].project_id = "test-project"

        orchestrator = OrchestrateAgent()
        return orchestrator, instances

    def test_unsafe_prompt_stops_pipeline(self) -> None:
        """It returns the generic security error and stops the rest of the pipeline."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=False,
            category=SecurityCategory.DIRECT_IDENTIFIER_LOOKUP,
            reason="Direct record lookup by explicit identifier is not allowed.",
        )

        result = orchestrator.run_agent(
            input_question="Give me data from user with id = 20",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_type="TEXT",
            input_question_context=None,
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"], "Security Alert: Invalid or malicious query detected."
        )
        instances["router"].identify_context.assert_not_called()
        instances["query"].generate_sql.assert_not_called()
        instances["db"].get_schema.assert_not_called()
        instances["db"].execute_query.assert_not_called()
        instances["response"].generate_natural_language.assert_not_called()

    def test_safe_prompt_continues_pipeline(self) -> None:
        """It continues through the normal pipeline when the prompt is safe."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )
        instances["db"].get_schema.return_value = {
            "id_empresa": "INTEGER",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.return_value = (
            "SELECT id_empresa FROM test_ia.passagens_aereas"
        )
        instances["db"].execute_query.return_value = [{"id_empresa": 1}]
        instances["response"].generate_natural_language.return_value = "ok"

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost this month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_type="TEXT",
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        instances["router"].identify_context.assert_not_called()
        instances["query"].generate_sql.assert_called_once()
        instances["db"].get_schema.assert_called_once()
        instances["db"].execute_query.assert_called_once()
        instances["response"].generate_natural_language.assert_called_once()
