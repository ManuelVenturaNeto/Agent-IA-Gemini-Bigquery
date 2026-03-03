import unittest

from src.agents.query_agent.tool_kit import validate_sql_rules


class ValidateSqlRulesTests(unittest.TestCase):
    """Tests for local SQL validation before execution."""

    def test_rejects_multi_statement_sql(self) -> None:
        """It blocks SQL scripts so chat prompts cannot inject extra statements."""
        validation = validate_sql_rules(
            "SELECT company_id FROM test; DROP TABLE test"
        )

        self.assertEqual(
            validation,
            "VIOLATION: Multiple statements are not allowed.",
        )

    def test_allows_count_star_when_select_star_is_not_used(self) -> None:
        """It allows aggregate expressions such as COUNT(*) while still requiring company_id."""
        validation = validate_sql_rules(
            "SELECT company_id, COUNT(*) AS total FROM test GROUP BY company_id"
        )

        self.assertEqual(validation, "VALID: SQL meets all rules.")

    def test_rejects_scope_column_when_only_used_in_where_clause(self) -> None:
        """It requires company_id in the top-level SELECT list, not only in filters."""
        validation = validate_sql_rules(
            "SELECT COUNT(*) AS total FROM test WHERE company_id = 1"
        )

        self.assertEqual(
            validation,
            "VIOLATION: Query must select 'company_id'.",
        )
