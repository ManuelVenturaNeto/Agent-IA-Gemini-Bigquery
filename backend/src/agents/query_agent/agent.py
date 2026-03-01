from src.agents.base import BaseAgent

from .tool_kit import build_query_toolkit, validate_sql_rules


class QueryAgent(BaseAgent):
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
    ) -> str:
        feedback = "Generate the SQL now."
        last_validation = "VIOLATION: SQL was not generated."

        for _ in range(3):
            sql = self._clean_sql(
                self._chain.invoke(
                    {
                        "schemas": str(tables_and_schemas),
                        "input": question_text,
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
        raise ValueError(f"Unable to generate valid SQL after 3 attempts. {last_validation}")
