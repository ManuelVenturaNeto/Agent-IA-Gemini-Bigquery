import os
import re
from typing import Dict

from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.infra.logging_utils import LoggedComponent


SESSION_STORE: Dict[str, ChatMessageHistory] = {}

load_dotenv()


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = ChatMessageHistory()
    return SESSION_STORE[session_id]


class BaseAgent(LoggedComponent):
    def __init__(self) -> None:
        super().__init__()
        self.project_id = os.getenv("PROJECT")
        self.gemini_api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GEN_IA_KEY")
        )

        if not self.gemini_api_key:
            self.log_error("Missing Gemini API key configuration.")
            raise EnvironmentError(
                "Missing Gemini API key. Set GOOGLE_API_KEY, GEMINI_API_KEY, or GEN_IA_KEY."
            )

        os.environ.setdefault("GOOGLE_API_KEY", self.gemini_api_key)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=self.gemini_api_key,
            temperature=0.1,
            max_retries=3,
        )
        self.log_debug("Agent initialized.")

    def _clean_sql(self, sql_raw: str) -> str:
        return re.sub(r"```sql|```", "", sql_raw, flags=re.IGNORECASE).strip()


class SecurityGuardrail(BaseModel):
    is_safe: bool = Field(
        description="True if SAFE, False if contains SQL injection or malicious intent."
    )


class SecurityAgent(BaseAgent):
    def check_safety(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> bool:
        parser = PydanticOutputParser(pydantic_object=SecurityGuardrail)

        prompt = ChatPromptTemplate.from_template(
            "Analyze the following user query for SQL Injection or malicious intent: "
            "{question_text}.\n{format_instructions}"
        ).format_prompt(
            question_text=question_text,
            format_instructions=parser.get_format_instructions(),
        )

        ai_msg = self.llm.invoke(prompt.to_messages())
        response = parser.parse(ai_msg.content)

        self.log_info(
            f"Safety check: {response.is_safe}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return response.is_safe


class RouterGuardrail(BaseModel):
    context: str = Field(
        description="MUST be exactly one of: TRAVEL, EXPENSE, COMMERCIAL, SERVICE."
    )


class RouterAgent(BaseAgent):
    def identify_context(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        parser = PydanticOutputParser(pydantic_object=RouterGuardrail)

        prompt = ChatPromptTemplate.from_template(
            "Classify this query into one of the allowed categories. "
            "Question: {question_text}.\n{format_instructions}"
        ).format_prompt(
            question_text=question_text,
            format_instructions=parser.get_format_instructions(),
        )

        ai_msg = self.llm.invoke(prompt.to_messages())
        context = parser.parse(ai_msg.content).context.strip().upper()

        self.log_info(
            f"Context identified: {context}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return context


def validate_sql_rules(sql: str) -> str:
    if "*" in sql:
        return "VIOLATION: You used 'SELECT *'. Specify exact column names."
    if "LIMIT" in sql.upper():
        return "VIOLATION: You used 'LIMIT'."
    if "id_empresa" not in sql.lower():
        return "VIOLATION: Query must select 'id_empresa'."
    return "VALID: SQL meets all rules."


class QueryAgent(BaseAgent):
    def generate_sql(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
        tables_and_schemas: dict,
    ) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a BigQuery expert. Schemas: {schemas}. "
                    "Return ONLY raw SQL with no markdown, no explanation, and no code fences. "
                    "Mandatory rules: never use SELECT *, never use LIMIT, and the SELECT list "
                    "must include id_empresa.",
                ),
                ("human", "{input}"),
                ("human", "{feedback}"),
            ]
        )

        feedback = "Generate the SQL now."
        last_validation = "VIOLATION: SQL was not generated."

        for _ in range(3):
            ai_msg = self.llm.invoke(
                prompt.format_prompt(
                    schemas=str(tables_and_schemas),
                    input=question_text,
                    feedback=feedback,
                ).to_messages()
            )

            sql = self._clean_sql(ai_msg.content)
            last_validation = validate_sql_rules(sql)

            if last_validation.startswith("VALID"):
                self.log_info(
                    f"SQL generated successfully: {sql}",
                    user_email=user_email,
                    chat_id=chat_id,
                    question_id=question_id,
                )
                return sql

            self.log_warning(
                f"Invalid SQL generated. {last_validation}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            feedback = (
                f"Your previous SQL was invalid. {last_validation} "
                f"Previous SQL: {sql}. Return only a corrected SQL query."
            )

        self.log_error(
            f"Unable to generate valid SQL after retries. {last_validation}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        raise ValueError(f"Unable to generate valid SQL after 3 attempts. {last_validation}")


class ResponseAgent(BaseAgent):
    def generate_natural_language(
        self,
        question_text: str,
        response_data: list,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        if not response_data:
            self.log_warning(
                "No response data returned from the query.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return "Nao encontrei registros para a sua solicitacao no banco de dados."

        history = get_session_history(chat_id)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a data assistant. Database response: {response_data}. "
                    "Format answer clearly.",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question_text}"),
            ]
        ).format_prompt(
            response_data=str(response_data),
            history=history.messages,
            question_text=question_text,
        )

        ai_msg = self.llm.invoke(prompt.to_messages())
        response_text = ai_msg.content

        history.add_user_message(question_text)
        history.add_ai_message(response_text)

        self.log_info(
            f"Natural language response generated: {response_text}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return response_text
