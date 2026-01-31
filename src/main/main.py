import logging
from enum import Enum
from src.agents.query_agent import ResponseAgent, RouterAgent, SecurityAgent, QueryAgent
from src.infra.config.config_google.bigquery_maganger import BigQueryManager


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


class OrchestrateAgent:
    """
    Orchestrate Agent - Manager of the multi-agent workflow
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self.log.debug("MainPipeline Initialized")

        self.security = SecurityAgent()
        self.router = RouterAgent()
        self.query_specialist = QueryAgent()
        self.responder = ResponseAgent()
        self.db = BigQueryManager()
        self.project_id = self.db.project_id

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
            user_email = input_user
            question_text = input_question
            chat_id = input_chat_id
            question_id = input_question_id
            question_context = input_question_context if input_question_context else None
            response_type = input_response_type if input_question_context else 'TEXT'  # SQL, TEXT, GRAPHIC

            self.log.info("Starting orchestration for: %s", user_email)

            is_safe = self.security.check_safety(
                question_text=question_text,
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )

            if not is_safe:
                self.log.warning(
                    "[WARNING] Security breach attempt detected from %s on question_id: %s in chat_id: %s",
                    user_email,
                    question_id,
                    chat_id,
                )
                return {
                    "status": "error",
                    "message": "Security Alert: Invalid or malicious query detected.",
                }

            question_contexts = list(QuestionContext)

            if question_context and question_context.upper() in question_contexts:
                context = QuestionContext(question_context.upper())
                self.log.debug("[DEBUG] Using provided context: %s", context)

            else:
                context = self.router.identify_context(
                    question_text=question_text,
                    user_email=user_email,
                    chat_id=chat_id,
                    question_id=question_id,
                )
                self.log.debug("[DEBUG] Context identified by router: %s", context)

            if context in question_contexts:

                table_list: list[str] = TableList[context].value

                if not table_list:
                    self.log.warning("Context %s has no configured tables.", context)
                    return {
                        "status": "error",
                        "message": f"Context {context.value} has no configured tables.",
                        "context": context.value,
                    }

                tables_and_schemas = {}

                for table_id in table_list:
                    
                    db_schema = self.db.get_schema(
                        table_id=f"{self.project_id}.{table_id}"
                    )

                    tables_and_schemas[table_id] = db_schema

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
                )

                response_natural_language = self.responder.generate_natural_language(
                    question_text=question_text,
                    response_data=response_data,
                    user_email=user_email,
                    chat_id=chat_id,
                    question_id=question_id,
                )

                self.log.info("Pipeline execution finished successfully")
                return {
                    "status": "success",
                    "context": context,
                    "response_type": response_type,
                    "response_sql": response_sql,
                    "response_data": response_data,
                    "response_natural_language": response_natural_language,
                }

            self.log.warning("Context %s not yet implemented.", context)

            return {
                "status": "error",
                "message": f"Context {context} is under development.",
                "context": context,
            }

        except Exception as exp:
            self.log.critical("Fatal system failure in Orchestrator: %s", exp)
            return {
                "status": "error",
                "message": f"Error: {exp}",
            }
