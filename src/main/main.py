from enum import Enum

from src.agents.query_agent import QueryAgent, ResponseAgent, RouterAgent, SecurityAgent
from src.infra.config.config_google.bigquery_maganger import BigQueryManager
from src.infra.logging_utils import LoggedComponent


class QuestionContext(str, Enum):
    TRAVEL = "TRAVEL"
    EXPENSE = "EXPENSE"
    COMMERCIAL = "COMMERCIAL"
    SERVICE = "SERVICE"


class ResponseType(str, Enum):
    SQL = "SQL"
    TEXT = "TEXT"
    GRAPHIC = "GRAPHIC"


class TableList(Enum):
    TRAVEL = ["test_ia.passagens_aereas"]
    EXPENSE = ["test_ia.despesas"]
    COMMERCIAL = []
    SERVICE = []


class OrchestrateAgent(LoggedComponent):
    """
    Orchestrate Agent - Manager of the multi-agent workflow
    """

    def __init__(self) -> None:
        super().__init__()
        self.log_debug("Main pipeline initialized.")
        self.security = SecurityAgent()
        self.router = RouterAgent()
        self.query_specialist = QueryAgent()
        self.responder = ResponseAgent()
        self.db = BigQueryManager()
        self.project_id = self.db.project_id

    @staticmethod
    def _available_contexts() -> set[str]:
        return {item.value for item in QuestionContext}

    def _normalize_request(
        self,
        input_question: str,
        input_user: str,
        input_chat_id: str,
        input_question_id: str,
        input_response_type: str | None,
        input_question_context: str | None,
    ) -> dict[str, str | None]:
        return {
            "user_email": input_user,
            "question_text": input_question,
            "chat_id": input_chat_id,
            "question_id": input_question_id,
            "question_context": input_question_context if input_question_context else None,
            "response_type": input_response_type if input_question_context else "TEXT",
        }

    def _reject_if_unsafe(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> dict[str, str] | None:
        is_safe = self.security.check_safety(
            question_text=question_text,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        if is_safe:
            return None

        self.log_warning(
            "Security breach attempt detected.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return {
            "status": "error",
            "message": "Security Alert: Invalid or malicious query detected.",
        }

    def _resolve_context_key(
        self,
        question_text: str,
        question_context: str | None,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        available_contexts = self._available_contexts()

        if question_context and question_context.upper() in available_contexts:
            context = QuestionContext(question_context.upper())
            self.log_debug(
                f"Using provided context: {context.value}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
        else:
            context = self.router.identify_context(
                question_text=question_text,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            self.log_debug(
                f"Context identified by router: {context}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

        return context.value if isinstance(context, QuestionContext) else str(context)

    def _build_tables_and_schemas(
        self,
        context_key: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> dict[str, dict[str, str]] | None:
        table_list: list[str] = TableList[context_key].value

        if not table_list:
            self.log_warning(
                f"Context {context_key} has no configured tables.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return None

        tables_and_schemas: dict[str, dict[str, str]] = {}

        for table_id in table_list:
            full_table_id = f"{self.project_id}.{table_id}"
            db_schema = self.db.get_schema(
                table_id=full_table_id,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            tables_and_schemas[table_id] = db_schema

        return tables_and_schemas

    def _run_context_pipeline(
        self,
        context_key: str,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
        response_type: str | None,
    ) -> dict[str, object]:
        tables_and_schemas = self._build_tables_and_schemas(
            context_key=context_key,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        if tables_and_schemas is None:
            return {
                "status": "error",
                "message": f"Context {context_key} has no configured tables.",
                "context": context_key,
            }

        response_sql = self.query_specialist.generate_sql(
            tables_and_schemas=tables_and_schemas,
            question_text=question_text,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        response_data = self.db.execute_query(
            response_sql=response_sql,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        response_natural_language = self.responder.generate_natural_language(
            question_text=question_text,
            response_data=response_data,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        self.log_info(
            "Pipeline execution finished successfully.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return {
            "status": "success",
            "context": context_key,
            "response_type": response_type,
            "response_sql": response_sql,
            "response_data": response_data,
            "response_natural_language": response_natural_language,
        }

    def run_agent(
        self,
        input_question: str,
        input_user: str,
        input_chat_id: str,
        input_question_id: str,
        input_response_type: str | None,
        input_question_context: str | None,
    ) -> dict[str, object]:
        """
        Executes the Multi-Agent Pipeline: Security -> Router -> SQL Specialist -> Response
        """
        try:
            request_data = self._normalize_request(
                input_question=input_question,
                input_user=input_user,
                input_chat_id=input_chat_id,
                input_question_id=input_question_id,
                input_response_type=input_response_type,
                input_question_context=input_question_context,
            )
            user_email = str(request_data["user_email"])
            question_text = str(request_data["question_text"])
            chat_id = str(request_data["chat_id"])
            question_id = str(request_data["question_id"])
            question_context = request_data["question_context"]
            response_type = request_data["response_type"]

            self.log_info(
                "Starting orchestration.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

            unsafe_response = self._reject_if_unsafe(
                question_text=question_text,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

            if unsafe_response:
                return unsafe_response

            context_key = self._resolve_context_key(
                question_text=question_text,
                question_context=question_context,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

            if context_key in self._available_contexts():
                return self._run_context_pipeline(
                    context_key=context_key,
                    question_text=question_text,
                    user_email=user_email,
                    chat_id=chat_id,
                    question_id=question_id,
                    response_type=response_type,
                )

            self.log_warning(
                f"Context {context_key} is not implemented.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return {
                "status": "error",
                "message": f"Context {context_key} is under development.",
                "context": context_key,
            }

        except Exception as exp:
            self.log_critical(
                f"Fatal system failure in Orchestrator: {exp}",
                user_email=input_user,
                chat_id=input_chat_id,
                question_id=input_question_id,
            )
            return {
                "status": "error",
                "message": f"Error: {exp}",
            }
