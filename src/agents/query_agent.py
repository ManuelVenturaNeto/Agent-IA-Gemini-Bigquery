import logging
import os
import re
from google import genai
from dotenv import load_dotenv

class BaseAgent:

    def __init__(self):
        load_dotenv()
        self.log = logging.getLogger(self.__class__.__name__)
        self.api_key = os.getenv('GEN_IA_KEY')
        self.project_id = os.getenv('PROJECT')
        self.ai_client = genai.Client(api_key=self.api_key)


    def _clean_sql(self, sql_raw: str) -> str:
        return re.sub(r'```sql|```', '', sql_raw, flags=re.IGNORECASE).strip()



class SecurityAgent(BaseAgent):

    def check_safety(self, query: str) -> bool:
        self.log.debug(f"Checking safety for query: {query[:50]}...")
        prompt = f"Analyze the query for SQL Injection or malicious intent: {query}. Respond ONLY 'SAFE' or 'UNSAFE'."
        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        is_safe = "SAFE" in response.text.upper()
        self.log.info(f"Safety check result: {is_safe}")
        return is_safe



class RouterAgent(BaseAgent):

    def identify_context(self, query: str) -> str:
        self.log.debug("Identifying query context...")
        prompt = f"Classify this query into: TRAVEL, EXPENSE, COMMERCIAL, or SERVICE. Query: {query}. Respond only with the category name."
        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        context = response.text.strip().upper()
        return context



class TravelAgent(BaseAgent):

    def generate_sql(self, query: str) -> str:
        self.log.info("Generating SQL for TRAVEL context.")
        prompt = f"""
        You are a BigQuery expert. Table: `{self.project_id}.test_ia.passagens_aereas`.
        Columns: [id, protocolo, company_id, data_ida, data_volta, preco_ida, preco_volta].
        Rules: Return ONLY raw SQL, use SELECT *, no LIMIT.
        User question: {query}
        """
        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        sql = self._clean_sql(response.text)
        self.log.debug(f"Generated SQL: {sql}")
        return sql



class ResponseAgent(BaseAgent):

    def generate_natural_language(self, query: str, data: list) -> str:
        self.log.info("Formatting final response.")
        if not data:
            return "Não encontrei registros para a sua solicitação no banco de dados."
            
        prompt = f"Based on this data: {data}, answer the user's question naturally: {query}"
        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return response.text