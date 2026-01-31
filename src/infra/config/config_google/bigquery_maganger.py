import logging
import os
from typing import Dict
from google.cloud.bigquery import Table, SchemaField
from google.cloud import bigquery
from dotenv import load_dotenv

class BigQueryManager:
    def __init__(self):
        load_dotenv()
        self.log = logging.getLogger(self.__class__.__name__)
        
        self.project_id = os.getenv('PROJECT')
        self.project_sa = os.getenv('PROJECT_SA')
        
        if not self.project_id or not self.project_sa:
            self.log.error("Missing GCP environment variables.")
            raise EnvironmentError("PROJECT or PROJECT_SA not set.")

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.project_sa
        self.bq_client = bigquery.Client(project=self.project_id)
        self.log.debug("BigQuery Client initialized.")

    def get_schema(self, table_id: list) -> Dict[str, str]:
        """
        Return a map of column name -> BigQuery type without running SQL.
        """
        table: Table = self.bq_client.get_table(table_id)

        schema_map: Dict[str, str] = {}
        for schema_field in table.schema:
            schema_field_typed: SchemaField = schema_field
            schema_map[schema_field_typed.name] = schema_field_typed.field_type

        return schema_map

    def execute_query(self, response_sql: str, user_email: str):
        """
        Wraps the AI-generated SQL in a secure CTE filter
        """
        secure_sql = f"""
        WITH query_ia AS (
            {response_sql}
        )
        SELECT * FROM query_ia
        WHERE id_empresa IN (
            SELECT id_empresa FROM `{self.project_id}.test_ia.usuarios` 
            WHERE email = '{user_email}'
        )
        """
        
        self.log.info(f"Executing secure query for {user_email}")
        
        job_config = bigquery.QueryJobConfig(
            use_query_cache=True,
            priority=bigquery.QueryPriority.INTERACTIVE,
        )

        try:
            query_job = self.bq_client.query(secure_sql, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            self.log.info(f"[INFO] [FROM: {user_email}] - Query successful. Rows returned: {len(results)}")

            return results

        except Exception as exp:
            self.log.error(f"BigQuery Execution Error: {exp}")
            raise exp