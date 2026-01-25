import logging
from src.agents.query_agent import SecurityAgent, RouterAgent, TravelAgent, ResponseAgent
from src.infra.config.config_google.bigquery_maganger import BigQueryManager

class OrchestrateAgent:
    """
    Orchestrate Agent - Manager of the multi-agent workflow
    """
    def __init__(self) -> None:
        self.log = logging.getLogger(__name__)
        self.log.debug("MainPipeline Initialized")

        self.security = SecurityAgent()
        self.router = RouterAgent()
        self.travel_specialist = TravelAgent()
        self.responder = ResponseAgent()
        self.db = BigQueryManager()



    def run_agent(self, input_question: str = None, input_user: str = None) -> str:
        """
        Executes the Multi-Agent Pipeline: Security -> Router -> SQL Specialist -> Response
        """
        try:
            user_email = input_user
            question_text = input_question

            self.log.info(f" Starting orchestration for: {user_email}")

            if not self.security.check_safety(question_text=question_text, user_email=user_email):
                self.log.warning(f"Security breach attempt detected from {user_email}")
                return "Security Alert: Invalid or malicious query detected."

            context = self.router.identify_context(question_text, user_email=user_email)
            self.log.info(f"Context identified: {context}")

            if context == "TRAVEL":
                sql_ia = self.travel_specialist.generate_sql(question_text=question_text, user_email=user_email)

                data = self.db.execute_query(sql_ia=sql_ia, user_email=user_email)

                final_answer = self.responder.generate_natural_language(question_text=question_text, data=data, user_email=user_email)

                self.log.info("Pipeline execution finished successfully")
                return final_answer
            
            self.log.warning(f"Context {context} not yet implemented.")
            return f"Context {context} is under development."

        except Exception as exp:
            self.log.critical(f"Fatal system failure in Orchestrator: {exp}")
            return f"Error: {exp}"