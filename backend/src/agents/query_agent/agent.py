import re
from typing import Optional

from src.agents.base import BaseAgent

from .tool_kit import build_query_toolkit, validate_sql_rules


class QueryAgent(BaseAgent):
    _IDENTIFIER_PATTERNS = (
        re.compile(
            r"\b(?:eu\s+sou(?:\s+o)?|i\s+am|i'm|my|meu|minha)?\s*"
            r"(?:user|usuario|usuário|company|empresa)\s+id\s*"
            r"(?:=|:|is|e|é)?\s*[a-z0-9_-]+\b",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:email|e-mail)\s*(?:=|:|is|e|é)?\s*"
            r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
            flags=re.IGNORECASE,
        ),
    )

    def __init__(self) -> None:
        super().__init__()
        self._chain = build_query_toolkit(self.llm)

    def generate_sql(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
        tables_and_schemas: dict[str, dict[str, str]],
        retry_reason: Optional[str] = None,
        previous_sql: Optional[str] = None,
    ) -> str:
        sanitized_question = self._sanitize_question_text(question_text)
        feedback = self._build_feedback(
            retry_reason=retry_reason,
            previous_sql=previous_sql,
        )
        last_validation = "VIOLATION: SQL was not generated."

        for _ in range(3):
            sql = self._clean_sql(
                self._chain.invoke(
                    {
                        "schemas": str(tables_and_schemas),
                        "input": sanitized_question,
                        "feedback": feedback,
                    }
                )
            )
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
        raise ValueError(
            f"Unable to generate valid SQL after 3 attempts. {last_validation}"
        )

    def _sanitize_question_text(self, question_text: str) -> str:
        """Remove user-typed identifiers so self-service SQL relies on auth context."""
        sanitized_question = str(question_text or "")
        for pattern in self._IDENTIFIER_PATTERNS:
            sanitized_question = pattern.sub("", sanitized_question)

        sanitized_question = re.sub(r"\s+", " ", sanitized_question)
        sanitized_question = re.sub(r"\s+([,.;:!?])", r"\1", sanitized_question)
        sanitized_question = sanitized_question.strip(" ,.;:!?")
        return sanitized_question or str(question_text or "").strip()

    def _build_feedback(
        self,
        retry_reason: Optional[str],
        previous_sql: Optional[str],
    ) -> str:
        """Build the initial LLM feedback for first-pass generation or regeneration."""
        if not retry_reason:
            return "Generate the SQL now."

        previous_sql_text = previous_sql or "SQL not available."
        return (
            "Your previous SQL did not satisfy the request. "
            f"Issue detected: {retry_reason}. "
            f"Previous SQL: {previous_sql_text}. "
            "Use the same question and schemas to return only a corrected SQL query."
        )
