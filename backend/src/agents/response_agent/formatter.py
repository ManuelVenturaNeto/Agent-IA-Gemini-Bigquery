from typing import Any


ResponseRow = dict[str, Any]

ANALYTICAL_SIGNAL_WORDS = (
    "highlight",
    "highlights",
    "insight",
    "insights",
    "average",
    "mode",
    "outlier",
    "trend",
    "destaque",
    "destaques",
    "media",
    "moda",
    "outliers",
    "tendencia",
    "tendencias",
)


class ResponseReportFormatter:
    """Normalize model output into grounded readable prose."""

    def finalize_response(
        self,
        *,
        response_text: str,
        question_text: str,
        response_data: list[ResponseRow],
        serialized_rows: str,
        analysis_summary: str,
    ) -> str:
        """Return the best readable response for the given model output."""
        cleaned_response = str(response_text or "").strip()

        if not cleaned_response or self._looks_like_raw_dump(
            cleaned_response,
            serialized_rows,
        ):
            return self._build_fallback_report(
                question_text=question_text,
                response_data=response_data,
                analysis_summary=analysis_summary,
            )

        if analysis_summary and not self._contains_analytical_signals(cleaned_response):
            return f"{cleaned_response}\n\n{analysis_summary}"

        return cleaned_response

    def _contains_analytical_signals(self, response_text: str) -> bool:
        lowered = response_text.lower()
        return any(word in lowered for word in ANALYTICAL_SIGNAL_WORDS)

    def _looks_like_raw_dump(self, response_text: str, serialized_rows: str) -> bool:
        stripped_response = response_text.strip()
        stripped_rows = serialized_rows.strip()

        if stripped_response == stripped_rows:
            return True

        if (
            stripped_response.startswith("[")
            and stripped_response.endswith("]")
        ) or (
            stripped_response.startswith("{")
            and stripped_response.endswith("}")
        ):
            return True

        return False

    def _build_fallback_report(
        self,
        *,
        question_text: str,
        response_data: list[ResponseRow],
        analysis_summary: str,
    ) -> str:
        total_rows = len(response_data)
        first_row = (
            response_data[0]
            if response_data and isinstance(response_data[0], dict)
            else {}
        )
        columns = [str(key) for key in first_row.keys()]

        intro = (
            f"Com base nos dados retornados para a pergunta '{question_text}', "
            f"encontrei {total_rows} registro"
            f"{'' if total_rows == 1 else 's'}."
        )

        detail = self._build_field_summary(columns)
        example = self._build_example_paragraph(first_row, columns)

        return "\n\n".join(
            part for part in (intro, detail, analysis_summary, example) if part
        )

    def _build_field_summary(self, columns: list[str]) -> str:
        if not columns:
            return (
                "A consulta retornou registros, mas sem campos suficientes para montar "
                "um detalhamento mais especifico."
            )

        column_text = ", ".join(columns[:5])
        return (
            "Os principais campos disponiveis nesta consulta sao "
            f"{column_text}."
        )

    def _build_example_paragraph(
        self,
        first_row: ResponseRow,
        columns: list[str],
    ) -> str:
        if not first_row or not columns:
            return ""

        fragments = [
            f"{column}={first_row.get(column)}"
            for column in columns[:3]
        ]
        if not fragments:
            return ""

        values_text = ", ".join(fragments)
        return (
            "Como referencia, o primeiro registro mostra "
            f"{values_text}. Use esses dados como base para interpretar o resultado completo."
        )
