from enum import Enum
from typing import Any
from typing import Dict
from typing import Optional
from typing import Set
from src.agents import QueryAgent
from src.agents import ResponseAgent
from src.agents import RouterAgent
from src.agents import SecurityAgent
from src.agents.graph_agent import GraphAgent
from src.agents.security_agent.tool_kit import SecurityCategory
from src.api.models import normalize_response_types
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
    GRAPH = "GRAPH"


class TableList(Enum):
    TRAVEL = ["test_ia.air_tickets"]
    EXPENSE = ["test_ia.expenses"]
    COMMERCIAL = ["test_ia.companies"]
    SERVICE = ["test_ia.users"]


class QueryResultValidator:
    """Applies lightweight checks before the response agent sees query rows."""

    _ACCESS_SCOPE_COLUMN = "company_id"

    _SUMMARY_HINTS = (
        "how much",
        "total",
        "sum",
        "average",
        "avg",
        "count",
        "number of",
        "amount",
        "quanto",
        "quantos",
        "media",
        "valor total",
    )
    _BREAKDOWN_HINTS = (
        " by ",
        " per ",
        " each ",
        "daily",
        "weekly",
        "monthly",
        "yearly",
        "breakdown",
        "grouped",
        "group by",
        "por ",
        " cada ",
        "diario",
        "semanal",
        "mensal",
        "agrupado",
    )
    _DETAIL_HINTS = (
        "list",
        "show all",
        "every",
        "raw",
        "records",
        "rows",
        "detalhe",
        "detalhes",
        "linhas",
        "registros",
    )

    def validate(
        self,
        question_text: str,
        response_data: list[dict],
    ) -> Optional[str]:
        """Return a retry reason when the result shape is not useful enough."""
        if not response_data:
            return None

        if not all(isinstance(row, dict) for row in response_data):
            return "Query returned rows in an unexpected format."

        typed_rows = [row for row in response_data if isinstance(row, dict)]

        if self._contains_only_scope_column(typed_rows):
            return (
                "Query returned only company_id without any analytical metric "
                "or dimension."
            )

        if self._is_too_granular(question_text, typed_rows):
            return (
                "Query returned data at an inappropriate granularity for the "
                "question."
            )

        return None

    def _contains_only_scope_column(self, rows: list[dict[str, Any]]) -> bool:
        """Return True when every row only contains the access-scope column."""
        for row in rows:
            if any(
                key != self._ACCESS_SCOPE_COLUMN and self._has_meaningful_value(value)
                for key, value in row.items()
            ):
                return False

        return True

    def _is_too_granular(
        self,
        question_text: str,
        rows: list[dict[str, Any]],
    ) -> bool:
        """Use question hints to reject result sets that are too detailed."""
        normalized_question = f" {question_text.strip().lower()} "
        row_count = len(rows)

        if self._contains_hint(normalized_question, self._DETAIL_HINTS):
            return False

        if self._contains_hint(normalized_question, self._SUMMARY_HINTS):
            if not self._contains_hint(normalized_question, self._BREAKDOWN_HINTS):
                return row_count > 5

        return (
            row_count > 50
            and not self._contains_hint(normalized_question, self._BREAKDOWN_HINTS)
        )

    def _contains_hint(
        self,
        normalized_question: str,
        hints: tuple[str, ...],
    ) -> bool:
        """Return True when one of the hint fragments exists in the question."""
        return any(hint in normalized_question for hint in hints)

    def _has_meaningful_value(self, value: Any) -> bool:
        """Return True for values that carry information beyond empty placeholders."""
        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        return True


class OrchestrateAgent(LoggedComponent):
    """Manages the multi-agent workflow from safety checks to response generation."""

    _MAX_QUERY_REGENERATION_ATTEMPTS = 3
    _MAX_QUERY_EXECUTION_RETRIES = 2

    def __init__(self) -> None:
        """Create all agents and shared infrastructure used by the pipeline."""
        super().__init__()
        self.log_debug("Main pipeline initialized.")
        self.security = SecurityAgent()
        self.router = RouterAgent()
        self.query_specialist = QueryAgent()
        self.responder = ResponseAgent()
        self.graph_agent = GraphAgent()
        self.db = BigQueryManager()
        self.result_validator = QueryResultValidator()
        self.project_id = self.db.project_id

    def _available_contexts(self) -> Set[str]:
        """Return the set of supported business contexts."""
        return {item.value for item in QuestionContext}

    def _normalize_request(
        self,
        input_question: str,
        input_user: str,
        input_chat_id: str,
        input_question_id: str,
        input_response_type: Optional[str],
        input_question_context: Optional[str],
        input_response_types: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Normalize raw request values into the shape used by the pipeline."""
        normalized_request = {
            "user_email": input_user,
            "question_text": input_question,
            "chat_id": input_chat_id,
            "question_id": input_question_id,
            "question_context": input_question_context if input_question_context else None,
            "response_types": normalize_response_types(
                response_types=input_response_types,
                response_type=input_response_type,
            ),
        }
        return normalized_request

    def _enabled_response_types(
        self,
        response_types: list[str],
    ) -> set[ResponseType]:
        """Return the enabled response types as enum values."""
        valid_values = {entry.value for entry in ResponseType}
        return {
            ResponseType(item)
            for item in response_types
            if item in valid_values
        }

    def _reject_if_unsafe(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> Optional[Dict[str, str]]:
        """Stop the pipeline early when the security decision is unsafe."""
        decision = self.security.check_safety(
            question_text=question_text,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        if decision.is_safe:
            return None

        if decision.category in (
            SecurityCategory.INVALID_INPUT,
            SecurityCategory.NON_BUSINESS_QUERY,
        ):
            self.log_warning(
                "Invalid non-business input detected. "
                f"category={decision.category} reason={decision.reason}",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return {
                "status": "error",
                "message": "Invalid input. Ask a clear business-related question.",
            }

        self.log_warning(
            "Security breach attempt detected. "
            f"category={decision.category} reason={decision.reason}",
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
        question_context: Optional[str],
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        """Resolve the context from the request or from the router agent."""
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
    ) -> Optional[Dict[str, Dict[str, str]]]:
        """Load schemas for all tables configured for the selected context."""
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
        response_types: list[str],
    ) -> Dict[str, Any]:
        """Run SQL generation, query execution, and response formatting."""
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

        response_sql, response_data = self._generate_and_execute_query(
            tables_and_schemas=tables_and_schemas,
            question_text=question_text,
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )

        enabled_types = self._enabled_response_types(response_types)
        response_natural_language = ""
        if ResponseType.TEXT in enabled_types:
            response_natural_language = self.responder.generate_natural_language(
                question_text=question_text,
                response_data=response_data,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

        graph_suggestions: list[dict[str, str]] = []
        if ResponseType.GRAPH in enabled_types:
            graph_suggestions = self.graph_agent.suggest_graphs(response_data)

        self.log_info(
            "Pipeline execution finished successfully.",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return {
            "status": "success",
            "context": context_key,
            "response_types": response_types,
            "response_sql": (
                response_sql if ResponseType.SQL in enabled_types else ""
            ),
            "response_data": response_data,
            "response_natural_language": response_natural_language,
            "graph_suggestions": graph_suggestions,
            "graph_path": "",
            "selected_graph_pattern": "",
        }

    def _generate_and_execute_query(
        self,
        tables_and_schemas: dict[str, dict[str, str]],
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> tuple[str, list[dict]]:
        """Generate SQL, retry execution, and regenerate SQL with DB errors when needed."""
        retry_reason: Optional[str] = None
        previous_sql: Optional[str] = None

        for generation_attempt in range(1, self._MAX_QUERY_REGENERATION_ATTEMPTS + 1):
            response_sql = self.query_specialist.generate_sql(
                tables_and_schemas=tables_and_schemas,
                question_text=question_text,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
                retry_reason=retry_reason,
                previous_sql=previous_sql,
            )

            for execution_attempt in range(1, self._MAX_QUERY_EXECUTION_RETRIES + 1):
                try:
                    response_data = self.db.execute_query(
                        response_sql=response_sql,
                        user_email=user_email,
                        chat_id=chat_id,
                        question_id=question_id,
                    )
                except Exception as exp:
                    retry_reason = f"Database execution error: {exp}"
                    previous_sql = response_sql
                    self.log_warning(
                        "Query execution failed. "
                        f"generation_attempt={generation_attempt} "
                        f"execution_attempt={execution_attempt} "
                        f"error={retry_reason}",
                        user_email=user_email,
                        chat_id=chat_id,
                        question_id=question_id,
                    )
                    continue

                validation_issue = self.result_validator.validate(
                    question_text=question_text,
                    response_data=response_data,
                )

                if validation_issue is None:
                    return response_sql, response_data

                retry_reason = validation_issue
                previous_sql = response_sql
                self.log_warning(
                    "Query result rejected. "
                    f"generation_attempt={generation_attempt} "
                    f"reason={retry_reason}",
                    user_email=user_email,
                    chat_id=chat_id,
                    question_id=question_id,
                )
                break

            self.log_warning(
                "Regenerating SQL after query failure or invalid result set.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

        raise RuntimeError(
            "Unable to produce a valid analytical result after SQL regeneration "
            f"attempts. Last issue: {retry_reason or 'Unknown query processing error.'}"
        )

    def run_agent(
        self,
        input_question: str,
        input_user: str,
        input_chat_id: str,
        input_question_id: str,
        input_response_type: Optional[str] = None,
        input_question_context: Optional[str] = None,
        input_response_types: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Execute the pipeline from safety validation through final response generation."""
        try:
            request_data = self._normalize_request(
                input_question=input_question,
                input_user=input_user,
                input_chat_id=input_chat_id,
                input_question_id=input_question_id,
                input_response_type=input_response_type,
                input_question_context=input_question_context,
                input_response_types=input_response_types,
            )
            user_email = str(request_data["user_email"])
            question_text = str(request_data["question_text"])
            chat_id = str(request_data["chat_id"])
            question_id = str(request_data["question_id"])
            question_context = request_data["question_context"]
            response_types = list(request_data["response_types"])

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
                    response_types=response_types,
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
