import logging
from google.cloud import bigquery
from src.infra.settings import settings


class BigQueryManager:
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

        self.project_id = settings.PROJECT
        self.project_sa = settings.PROJECT_SA

        self.bq_client = bigquery.Client(project=self.project_id)
        self.log.debug("BigQuery Client initialized.")



    def execute_query(self, sql_ia: str, user_email: str):
        """
        Wraps the AI-generated SQL in a secure CTE filter
        """
        secure_sql = f"""
        WITH query_ia AS (
            {sql_ia}
        )
        SELECT * FROM query_ia
        WHERE company_id IN (
            SELECT company_id FROM `{self.project_id}.test_ia.users` 
            WHERE email = @email_param
        )
        """
        
        self.log.info(f"Executing secure query for {user_email}")
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email_param", "STRING", user_email)
            ]
        )

        try:
            query_job = self.bq_client.query(secure_sql, job_config=job_config)
            results = [dict(row) for row in query_job.result()]
            self.log.info(f"Query successful. Rows returned: {len(results)}")

            return results

        except Exception as exp:
            self.log.error(f"BigQuery Execution Error: {exp}")
            raise exp