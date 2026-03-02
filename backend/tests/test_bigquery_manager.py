import unittest
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

from src.infra.config.config_google.bigquery_maganger import BigQueryManager


class BigQueryManagerExecuteQueryTests(unittest.TestCase):
    """Tests for safe SQL execution setup."""

    def test_uses_parameterized_email_filter(self) -> None:
        """It passes the login-derived email as a query parameter instead of interpolating it."""
        manager = BigQueryManager.__new__(BigQueryManager)
        manager.project_id = "test-project"
        manager.bq_client = Mock()
        manager.log_info = Mock()
        manager.log_error = Mock()

        query_job = Mock()
        query_job.result.return_value = [{"id_empresa": 1}]
        manager.bq_client.query.return_value = query_job

        with patch(
            "src.infra.config.config_google.bigquery_maganger.bigquery.QueryJobConfig",
            return_value="job-config",
        ) as job_config_class, patch(
            "src.infra.config.config_google.bigquery_maganger.bigquery.ScalarQueryParameter",
            return_value="email-param",
        ) as scalar_parameter:
            result = manager.execute_query(
                response_sql="SELECT id_empresa FROM test",
                user_email="o'hara@example.com",
                chat_id="chat-1",
                question_id="question-1",
            )

        executed_sql = manager.bq_client.query.call_args.args[0]
        self.assertIn("@user_email", executed_sql)
        self.assertNotIn("o'hara@example.com", executed_sql)
        self.assertEqual(result, [{"id_empresa": 1}])

        scalar_parameter.assert_called_once_with(
            "user_email",
            "STRING",
            "o'hara@example.com",
        )
        job_config_class.assert_called_once_with(
            use_query_cache=True,
            priority=ANY,
            query_parameters=["email-param"],
        )
