import os
import re
from typing import Dict

from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

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
        self.log_debug("LangChain agent initialized.")

    def _clean_sql(self, sql_raw: str) -> str:
        return re.sub(r"```sql|```", "", sql_raw, flags=re.IGNORECASE).strip()
