from dataclasses import dataclass
import json
from typing import Any

from src.agents.base import BaseAgent, get_session_history

from .analysis import AnalyticalSummaryBuilder
from .formatter import ResponseReportFormatter
from .tool_kit import build_response_toolkit


ResponseRow = dict[str, Any]

NO_DATA_MESSAGE = "Nao encontrei registros para a sua solicitacao no banco de dados."


@dataclass(frozen=True)
class ResponseDraft:
    """Hold the deterministic context used by the response agent."""

    question_text: str
    response_data: list[ResponseRow]
    serialized_rows: str
    analysis_summary: str

    def to_prompt_payload(self, history_messages: list[object]) -> dict[str, object]:
        return {
            "response_data": self.serialized_rows,
            "analysis_summary": self.analysis_summary,
            "history": history_messages,
            "question_text": self.question_text,
        }


class ResponseAgent(BaseAgent):
    """Generate readable analytical summaries from structured query results."""

    def __init__(self) -> None:
        super().__init__()
        self._chain = build_response_toolkit(self.llm)
        self._summary_builder = AnalyticalSummaryBuilder()
        self._report_formatter = ResponseReportFormatter()

    def generate_natural_language(
        self,
        question_text: str,
        response_data: list[ResponseRow],
        user_email: str,
        chat_id: str,
        question_id: str,
    ) -> str:
        """Generate a grounded natural-language answer for the returned rows."""
        if not response_data:
            self.log_warning(
                "No response data returned from the query.",
                user_email=user_email,
                chat_id=chat_id,
                question_id=question_id,
            )
            return NO_DATA_MESSAGE

        draft = self._build_response_draft(
            question_text=question_text,
            response_data=response_data,
        )
        history = get_session_history(chat_id)
        response_text = self._chain.invoke(
            draft.to_prompt_payload(history.messages)
        )
        final_response = self._finalize_response(
            response_text=response_text,
            draft=draft,
        )

        self._record_history(
            history=history,
            question_text=question_text,
            final_response=final_response,
        )
        self.log_info(
            f"Natural language response generated: {final_response}",
            user_email=user_email,
            chat_id=chat_id,
            question_id=question_id,
        )
        return final_response

    def _build_response_draft(
        self,
        *,
        question_text: str,
        response_data: list[ResponseRow],
    ) -> ResponseDraft:
        return ResponseDraft(
            question_text=question_text,
            response_data=response_data,
            serialized_rows=self._serialize_response_data(response_data),
            analysis_summary=self._get_summary_builder().build_summary(response_data),
        )

    def _serialize_response_data(self, response_data: list[ResponseRow]) -> str:
        """Return a stable JSON representation of the rows for prompt grounding."""
        return json.dumps(response_data, ensure_ascii=False, default=str)

    def _finalize_response(
        self,
        *,
        response_text: str,
        draft: ResponseDraft,
    ) -> str:
        return self._get_report_formatter().finalize_response(
            response_text=response_text,
            question_text=draft.question_text,
            response_data=draft.response_data,
            serialized_rows=draft.serialized_rows,
            analysis_summary=draft.analysis_summary,
        )

    def _record_history(
        self,
        *,
        history: object,
        question_text: str,
        final_response: str,
    ) -> None:
        history.add_user_message(question_text)
        history.add_ai_message(final_response)

    def _get_summary_builder(self) -> AnalyticalSummaryBuilder:
        builder = getattr(self, "_summary_builder", None)
        if builder is None:
            builder = AnalyticalSummaryBuilder()
            self._summary_builder = builder
        return builder

    def _get_report_formatter(self) -> ResponseReportFormatter:
        formatter = getattr(self, "_report_formatter", None)
        if formatter is None:
            formatter = ResponseReportFormatter()
            self._report_formatter = formatter
        return formatter
