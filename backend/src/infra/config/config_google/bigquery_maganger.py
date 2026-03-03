import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField, Table
from src.infra.logging_utils import LoggedComponent


class BigQueryManager(LoggedComponent):
    """Handles BigQuery interactions, including schema retrieval and query execution."""

    def __init__(self) -> None:
        env_path = Path(__file__).resolve().parents[4] / ".env"
        load_dotenv(env_path)
        super().__init__()
        self.project_id = (
            os.getenv("PROJECT_ID")
            or os.getenv("PROJECT")
            or ""
        ).strip()
        self.project_sa = self._resolve_service_account_path(env_path)

        if not self.project_id or not self.project_sa:
            self.log_error("Missing GCP environment variables.")
            raise EnvironmentError("PROJECT_ID/PROJECT or PROJECT_SA not set.")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.project_sa
        self.bq_client = bigquery.Client(project=self.project_id)
        self.log_debug("BigQuery client initialized.")

    def get_schema(
        self,
        table_id: str,
        user_email: str | None = None,
        chat_id: str | None = None,
        question_id: str | None = None,
    ) -> Dict[str, str]:
        """
        Return a map of column name -> BigQuery type without running SQL.
        """
        self.log_info(
            f"Loading schema for table {table_id}.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        table: Table = self.bq_client.get_table(table_id)

        schema_map: Dict[str, str] = {}
        for schema_field in table.schema:
            schema_field_typed: SchemaField = schema_field
            schema_map[schema_field_typed.name] = schema_field_typed.field_type

        self.log_info(
            f"Schema loaded for table {table_id}. Columns: {len(schema_map)}.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return schema_map

    def execute_query(
        self,
        response_sql: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> list[dict]:
        """
        Wrap the AI-generated SQL in a company-scoped access filter.
        """
        secure_sql = f"""
        WITH scoped_user AS (
            SELECT company_id
            FROM `{self.project_id}.test_ia.users`
            WHERE LOWER(email) = LOWER(@user_email)
        ),
        query_ia AS (
            {response_sql}
        )
        SELECT *
        FROM query_ia
        WHERE company_id IN (
            SELECT company_id
            FROM scoped_user
        )
        """

        self.log_info(
            "Executing secure BigQuery query.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        self.log_debug(
            f"Wrapped BigQuery SQL: {secure_sql}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        job_config = bigquery.QueryJobConfig(
            use_query_cache=True,
            priority=bigquery.QueryPriority.INTERACTIVE,
            query_parameters=[
                bigquery.ScalarQueryParameter("user_email", "STRING", user_email)
            ],
        )

        try:
            query_job = self.bq_client.query(secure_sql, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            self.log_info(
                f"Query successful. Rows returned: {len(results)}.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return results

        except Exception as exp:
            self.log_error(
                f"BigQuery execution error: {exp}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            raise

    def _resolve_service_account_path(self, env_path: Path) -> str:
        """Return an absolute service-account path from PROJECT_SA."""
        raw_value = os.getenv("PROJECT_SA", "").strip()
        if not raw_value:
            return ""

        candidate_path = Path(raw_value)
        if candidate_path.is_absolute():
            return str(candidate_path)

        return str((env_path.parent / candidate_path).resolve())
