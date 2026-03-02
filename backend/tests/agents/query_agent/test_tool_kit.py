import unittest

from src.agents.query_agent.tool_kit import validate_sql_rules


class ValidateSqlRulesTests(unittest.TestCase):
    """Tests for local SQL validation before execution."""

    def test_rejects_multi_statement_sql(self) -> None:
        """It blocks SQL scripts so chat prompts cannot inject extra statements."""
        validation = validate_sql_rules(
            "SELECT id_empresa FROM test; DROP TABLE test"
        )

        self.assertEqual(
            validation,
            "VIOLATION: Multiple statements are not allowed.",
        )

    def test_allows_count_star_when_select_star_is_not_used(self) -> None:
        """It allows aggregate expressions such as COUNT(*) while still requiring id_empresa."""
        validation = validate_sql_rules(
            "SELECT id_empresa, COUNT(*) AS total FROM test GROUP BY id_empresa"
        )

        self.assertEqual(validation, "VALID: SQL meets all rules.")
