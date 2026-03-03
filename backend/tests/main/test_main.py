import unittest
from unittest.mock import call
from unittest.mock import patch
from src.agents.security_agent.tool_kit import SecurityCategory
from src.agents.security_agent.tool_kit import SecurityDecision
from src.main.main import OrchestrateAgent
from src.main.main import QueryResultValidator


class QueryResultValidatorTests(unittest.TestCase):
    """Tests for post-query result validation."""

    def test_rejects_scope_only_rows(self) -> None:
        """It rejects rows that only contain the access-scope column."""
        validator = QueryResultValidator()

        issue = validator.validate(
            question_text="How much did my travel expenses cost this month?",
            response_data=[{"company_id": 1}],
        )

        self.assertEqual(
            issue,
            "Query returned only company_id without any analytical metric or dimension.",
        )

    def test_rejects_overly_granular_summary_result(self) -> None:
        """It rejects a summary question that returns too many detailed rows."""
        validator = QueryResultValidator()

        issue = validator.validate(
            question_text="How much did my travel expenses cost this month?",
            response_data=[
                {"company_id": 1, "total": 10},
                {"company_id": 1, "total": 20},
                {"company_id": 1, "total": 30},
                {"company_id": 1, "total": 40},
                {"company_id": 1, "total": 50},
                {"company_id": 1, "total": 60},
            ],
        )

        self.assertEqual(
            issue,
            "Query returned data at an inappropriate granularity for the question.",
        )

    def test_allows_breakdown_question_with_multiple_rows(self) -> None:
        """It allows multiple rows when the user explicitly asks for a breakdown."""
        validator = QueryResultValidator()

        issue = validator.validate(
            question_text="How much did my travel expenses cost by month?",
            response_data=[
                {"company_id": 1, "month": "2026-01", "total": 10},
                {"company_id": 1, "month": "2026-02", "total": 20},
                {"company_id": 1, "month": "2026-03", "total": 30},
                {"company_id": 1, "month": "2026-04", "total": 40},
                {"company_id": 1, "month": "2026-05", "total": 50},
                {"company_id": 1, "month": "2026-06", "total": 60},
            ],
        )

        self.assertIsNone(issue)


class OrchestrateAgentSecurityTests(unittest.TestCase):
    """Tests for orchestration behavior around the security gate."""

    def _build_orchestrator_with_mocks(self):
        """Create an orchestrator and expose its mocked collaborators."""
        patchers = {
            "graph": patch("src.main.main.GraphAgent"),
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

    def test_invalid_input_stops_pipeline(self) -> None:
        """It returns the invalid-input message and skips the rest of the pipeline."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=False,
            category=SecurityCategory.INVALID_INPUT,
            reason="Invalid input. Ask a clear business-related question.",
        )

        result = orchestrator.run_agent(
            input_question="test",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_type="TEXT",
            input_question_context=None,
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"], "Invalid input. Ask a clear business-related question."
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
            "company_id": "INTEGER",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.return_value = (
            "SELECT company_id, total FROM test_ia.air_tickets"
        )
        instances["db"].execute_query.return_value = [{"company_id": 1, "total": 125.0}]
        instances["response"].generate_natural_language.return_value = "ok"

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost this month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_types=["TEXT", "SQL"],
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        instances["router"].identify_context.assert_not_called()
        instances["query"].generate_sql.assert_called_once()
        instances["db"].get_schema.assert_called_once()
        instances["db"].execute_query.assert_called_once()
        instances["response"].generate_natural_language.assert_called_once()
        instances["graph"].suggest_graphs.assert_not_called()
        self.assertEqual(result["response_types"], ["TEXT", "SQL"])

    def test_sql_only_skips_natural_language_generation(self) -> None:
        """It skips the response agent when TEXT is not enabled."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )
        instances["db"].get_schema.return_value = {
            "company_id": "INTEGER",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.return_value = (
            "SELECT company_id, total FROM test_ia.air_tickets"
        )
        instances["db"].execute_query.return_value = [{"company_id": 1, "total": 125.0}]

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost this month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_types=["SQL"],
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["response_sql"], "SELECT company_id, total FROM test_ia.air_tickets")
        self.assertEqual(result["response_natural_language"], "")
        instances["response"].generate_natural_language.assert_not_called()

    def test_graph_mode_returns_suggestions_without_rendering_file(self) -> None:
        """It returns graph suggestions during /ask without rendering the final image."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )
        instances["db"].get_schema.return_value = {
            "company_id": "INTEGER",
            "month": "STRING",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.return_value = (
            "SELECT company_id, month, total FROM test_ia.air_tickets"
        )
        instances["db"].execute_query.return_value = [
            {"company_id": 1, "month": "2026-01", "total": 125.0}
        ]
        instances["graph"].suggest_graphs.return_value = [
            {
                "id": "bar_vertical",
                "label": "Bar",
                "reason": "Compares categories.",
                "x_field": "month",
                "y_field": "total",
                "hue_field": "",
            }
        ]

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost by month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_types=["GRAPH"],
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["response_sql"], "")
        self.assertEqual(result["response_natural_language"], "")
        self.assertEqual(result["graph_path"], "")
        self.assertEqual(result["selected_graph_pattern"], "")
        self.assertEqual(result["graph_suggestions"][0]["id"], "bar_vertical")
        instances["response"].generate_natural_language.assert_not_called()
        instances["graph"].suggest_graphs.assert_called_once()

    def test_query_execution_failure_regenerates_sql_with_db_error(self) -> None:
        """It retries execution, then regenerates SQL using the DB error and previous SQL."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )
        instances["db"].get_schema.return_value = {
            "company_id": "INTEGER",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.side_effect = [
            "SELECT company_id, FROM test_ia.air_tickets",
            "SELECT company_id, total FROM test_ia.air_tickets",
        ]
        instances["db"].execute_query.side_effect = [
            RuntimeError("Syntax error near FROM"),
            RuntimeError("Syntax error near FROM"),
            [{"company_id": 1, "total": 125.0}],
        ]
        instances["response"].generate_natural_language.return_value = "ok"

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost this month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_types=["TEXT"],
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(instances["query"].generate_sql.call_count, 2)
        self.assertEqual(instances["db"].execute_query.call_count, 3)
        instances["query"].generate_sql.assert_has_calls(
            [
                call(
                    tables_and_schemas={"test_ia.air_tickets": {"company_id": "INTEGER", "total": "FLOAT"}},
                    question_text="How much did my travel expenses cost this month?",
                    user_email="user@example.com",
                    chat_id="chat-1",
                    question_id="question-1",
                    retry_reason=None,
                    previous_sql=None,
                ),
                call(
                    tables_and_schemas={"test_ia.air_tickets": {"company_id": "INTEGER", "total": "FLOAT"}},
                    question_text="How much did my travel expenses cost this month?",
                    user_email="user@example.com",
                    chat_id="chat-1",
                    question_id="question-1",
                    retry_reason="Database execution error: Syntax error near FROM",
                    previous_sql="SELECT company_id, FROM test_ia.air_tickets",
                ),
            ]
        )

    def test_invalid_query_result_regenerates_sql_with_validation_reason(self) -> None:
        """It regenerates SQL when the returned rows are not useful enough."""
        orchestrator, instances = self._build_orchestrator_with_mocks()
        instances["security"].check_safety.return_value = SecurityDecision(
            is_safe=True,
            category=SecurityCategory.SAFE,
            reason="General analytical question.",
        )
        instances["db"].get_schema.return_value = {
            "company_id": "INTEGER",
            "total": "FLOAT",
        }
        instances["query"].generate_sql.side_effect = [
            "SELECT company_id FROM test_ia.air_tickets",
            "SELECT company_id, total FROM test_ia.air_tickets",
        ]
        instances["db"].execute_query.side_effect = [
            [{"company_id": 1}],
            [{"company_id": 1, "total": 125.0}],
        ]
        instances["response"].generate_natural_language.return_value = "ok"

        result = orchestrator.run_agent(
            input_question="How much did my travel expenses cost this month?",
            input_user="user@example.com",
            input_chat_id="chat-1",
            input_question_id="question-1",
            input_response_types=["TEXT"],
            input_question_context="TRAVEL",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(instances["query"].generate_sql.call_count, 2)
        self.assertEqual(instances["db"].execute_query.call_count, 2)
        instances["query"].generate_sql.assert_has_calls(
            [
                call(
                    tables_and_schemas={"test_ia.air_tickets": {"company_id": "INTEGER", "total": "FLOAT"}},
                    question_text="How much did my travel expenses cost this month?",
                    user_email="user@example.com",
                    chat_id="chat-1",
                    question_id="question-1",
                    retry_reason=None,
                    previous_sql=None,
                ),
                call(
                    tables_and_schemas={"test_ia.air_tickets": {"company_id": "INTEGER", "total": "FLOAT"}},
                    question_text="How much did my travel expenses cost this month?",
                    user_email="user@example.com",
                    chat_id="chat-1",
                    question_id="question-1",
                    retry_reason=(
                        "Query returned only company_id without any analytical metric "
                        "or dimension."
                    ),
                    previous_sql="SELECT company_id FROM test_ia.air_tickets",
                ),
            ]
        )
