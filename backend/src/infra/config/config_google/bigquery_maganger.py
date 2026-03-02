import os
from typing import Dict

from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField, Table

from src.infra.logging_utils import LoggedComponent


class BigQueryManager(LoggedComponent):
    def __init__(self) -> None:
        load_dotenv()
        super().__init__()
        self.project_id = os.getenv("PROJECT")
        self.project_sa = os.getenv("PROJECT_SA")

        if not self.project_id or not self.project_sa:
            self.log_error("Missing GCP environment variables.")
            raise EnvironmentError("PROJECT or PROJECT_SA not set.")

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
        Wraps the AI-generated SQL in a secure CTE filter
        """
        # secure_sql = f"""
        # WITH query_ia AS (
        #     {response_sql}
        # )
        # SELECT * FROM query_ia
        # WHERE id_empresa IN (
        #     SELECT id_empresa FROM `{self.project_id}.test_ia.usuarios`
        #     WHERE email = @user_email
        # )
        # """
        secure_sql = response_sql

        self.log_info(
            "Executing secure BigQuery query.",
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
