from src.agents.base import BaseAgent

from .tool_kit import build_router_toolkit


class RouterAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self._chain = build_router_toolkit(self.llm)

    def identify_context(
        self,
        question_text: str,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        context = self._chain.invoke({"question_text": question_text}).context.strip().upper()

        self.log_info(
            f"Context identified: {context}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return context
