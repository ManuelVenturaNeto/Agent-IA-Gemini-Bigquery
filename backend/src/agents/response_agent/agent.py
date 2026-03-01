from src.agents.base import BaseAgent, get_session_history

from .tool_kit import build_response_toolkit


class ResponseAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__()
        self._chain = build_response_toolkit(self.llm)

    def generate_natural_language(
        self,
        question_text: str,
        response_data: list,
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        if not response_data:
            self.log_warning(
                "No response data returned from the query.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return "Nao encontrei registros para a sua solicitacao no banco de dados."

        history = get_session_history(chat_id)
        response_text = self._chain.invoke(
            {
                "response_data": str(response_data),
                "history": history.messages,
                "question_text": question_text,
            }
        )

        history.add_user_message(question_text)
        history.add_ai_message(response_text)

        self.log_info(
            f"Natural language response generated: {response_text}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return response_text
