from src.agents.base import BaseAgent

from .tool_kit import build_security_toolkit


class SecurityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self._chain = build_security_toolkit(self.llm)

    def check_safety(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> bool:
        response = self._chain.invoke({"question_text": question_text})

        self.log_info(
            f"Safety check: {response.is_safe}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return bool(response.is_safe)
