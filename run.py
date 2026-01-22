import logging
import os
import re
from typing import List, Dict, Any, Union
from google import genai
from google.cloud import bigquery
from dotenv import load_dotenv

# Global Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

class BigQueryAgent:
    def __init__(self):
        load_dotenv()
        self.project_id = os.getenv('PROJECT')
        self.project_sa = os.getenv('PROJECT_SA')
        self.api_key = os.getenv('GEN_IA_KEY')

        self._validate_environment()

        # Set credentials and initialize clients
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.project_sa
        self.bq_client = bigquery.Client(project=self.project_id)
        self.ai_client = genai.Client(api_key=self.api_key)
        
        logging.info("Agent initialized successfully.")


    def _validate_environment(self):
        """
        Ensures all required environment variables are present
        """
        missing = [v for v in ['PROJECT', 'PROJECT_SA', 'GEN_IA_KEY'] if not os.getenv(v)]

        if missing:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing)}")


    def _clean_sql(self, sql_raw: str) -> str:
        """
        Removes markdown formatting and residual AI characters
        """
        sql = re.sub(r'```sql|```', '', sql_raw, flags=re.IGNORECASE)

        return sql.strip()


    def _generate_prompt(self, query: str) -> str:
        """
        Centralizes the prompt engineering logic
        """
        return f"""
        You are an expert in BigQuery SQL.
        Table: `{self.project_id}.test_ia.passagens_aereas`
        Available columns: [id, protocolo, company_id, data_ida, data_volta, preco_ida, preco_volta]

        CRITICAL RULES:
        1. Return ONLY the raw SQL code.
        2. Do NOT use LIMIT.
        3. Use 'SELECT *' to ensure external security filters work correctly.
        4. Ensure numeric filters like '>' are applied correctly.

        User question: {query}
        """


    def query(self, user_query: str, user_email: str) -> Union[List[Dict], str]:
        logging.info(f"Processing query: '{user_query}' for user {user_email}")

        # 1. SQL Generation via AI
        try:
            response = self.ai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=self._generate_prompt(user_query)
            )

            sql_ia = self._clean_sql(response.text)
            logging.info(f"AI Generated SQL:\n{sql_ia}")

        except Exception as e:
            logging.error(f"Failed to communicate with Gemini: {e}")
            return f"AI Error: {e}"

        # 2. Security Wrapper Construction
        # Using 'IN' to handle cases where an email might be associated with multiple company IDs
        secure_sql = f"""
        WITH query_ia AS (
            {sql_ia}
        )
        SELECT 
            * FROM query_ia
        WHERE company_id IN (
            SELECT 
                company_id 
            FROM `{self.project_id}.test_ia.users` 
            WHERE email = @email_param
        )
        """
        
        logging.info(f"Executing Final Query in BigQuery:\n{secure_sql}")

        # 3. BigQuery Execution
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("email_param", "STRING", user_email)
            ]
        )

        try:
            query_job = self.bq_client.query(secure_sql, job_config=job_config)
            results = query_job.result()

            # Data conversion and logging
            rows = [dict(row) for row in results]
            logging.info(f"Query executed. Total rows: {len(rows)}")
            
            if not rows:
                logging.warning(f"No data returned for the filter: {user_email}")
                
            return rows

        except Exception as e:
            logging.error(f"Query execution error: {e}")
            return f"BigQuery Error: {e}"



if __name__ == "__main__":
    try:
        agent = BigQueryAgent()
        
        test_user = "user050@empresa.com"
        test_query = "Which tickets cost more than 500 for the outbound flight?"
        
        results = agent.query(test_query, test_user)
        
        if isinstance(results, list):
            print(f"\n--- RESULTS FOUND ({len(results)}) ---")
            for r in results[:3]:
                print(r)
        else:
            print(f"\nFailure: {results}")
            
    except Exception as e:
        logging.critical(f"Fatal system failure: {e}")