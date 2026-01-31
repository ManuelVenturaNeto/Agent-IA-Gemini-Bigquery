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

    def check_safety(self, question_text: str, user_email: str, chat_id: str, question_id: str) -> bool:
        prompt = f"Analyze the query for SQL Injection or malicious intent: {question_text}. Respond ONLY 'SAFE' or 'UNSAFE'."

        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

        is_safe = "SAFE" in response.text.upper()

        self.log.info(f"[INFO] [FROM: {user_email} | CHAT_ID: {chat_id} | QUESTION_ID: {question_id}] - Safety check result: {is_safe}")

        return is_safe



class RouterAgent(BaseAgent):

    def identify_context(self, question_text: str, user_email: str, chat_id: str, question_id: str) -> str:
        prompt = f"Classify this query into: TRAVEL, EXPENSE, COMMERCIAL, or SERVICE. Question: {question_text}. Respond only with the category name."

        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

        context = response.text.strip().upper()

        self.log.info(f"[INFO] [FROM: {user_email} | CHAT_ID: {chat_id} | QUESTION_ID: {question_id}] - Identified context: {context}")

        return context



class QueryAgent(BaseAgent):

    def generate_sql(self, question_text: str, user_email: str, chat_id: str, question_id: str, tables_and_schemas: dict) -> str:
        prompt = f"""
        You are a BigQuery expert. 
        Tables and schemas: {tables_and_schemas}.
        Rules: Return ONLY raw SQL, use SELECT <columns>, dont use * and dont use LIMIT and every query should have the id_empresa column.
        User question: {question_text}
        """

        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

        sql = self._clean_sql(response.text)

        self.log.info(f"[INFO] [FROM: {user_email} | CHAT_ID: {chat_id} | QUESTION_ID: {question_id}] - Generated SQL: {sql}")

        return sql



class ResponseAgent(BaseAgent):

    def generate_natural_language(self, question_text: str, response_data: list, user_email: str, chat_id: str, question_id: str) -> str:
        if not response_data:
            return "Não encontrei registros para a sua solicitação no banco de dados."

        prompt = f"Based on this data: {response_data}, answer the user's question naturally: {question_text}"

        response = self.ai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

        self.log.info(f"[INFO] [FROM: {user_email} | CHAT_ID: {chat_id} | QUESTION_ID: {question_id}] - Response: {response.text}")

        return response.text