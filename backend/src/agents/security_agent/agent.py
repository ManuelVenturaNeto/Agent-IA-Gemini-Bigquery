from src.agents.base import BaseAgent
from .tool_kit import DirectIdentifierLookupDetector
from .tool_kit import SecurityDecision
from .tool_kit import SecurityToolkit


class SecurityAgent(BaseAgent):
    """Runs the local and model-based safety checks for a question."""

    def __init__(self) -> None:
        """Initialize the LLM toolkit used by the security agent."""
        super().__init__()
        self._detector = DirectIdentifierLookupDetector()
        self._toolkit = SecurityToolkit(self.llm)

    def check_safety(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> SecurityDecision:
        """Return the structured safety decision for the incoming prompt."""
        response = self._detector.detect(question_text)

        if response is None:
            response = self._toolkit.invoke(question_text)

        self.log_info(
            "Safety check: "
            f"{response.is_safe}, category: {response.category}, reason: {response.reason}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return response
