import json
from datetime import datetime

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
        serialized_rows = self._serialize_response_data(response_data)
        analysis_summary = self._build_analysis_summary(response_data)
        response_text = self._chain.invoke(
            {
                "response_data": serialized_rows,
                "analysis_summary": analysis_summary,
                "history": history.messages,
                "question_text": question_text,
            }
        )

        response_text = self._normalize_response_text(
            response_text=response_text,
            question_text=question_text,
            response_data=response_data,
            serialized_rows=serialized_rows,
            analysis_summary=analysis_summary,
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

    def _serialize_response_data(self, response_data: list) -> str:
        """Return a stable JSON representation of the rows for prompt grounding."""
        return json.dumps(response_data, ensure_ascii=False, default=str)

    def _normalize_response_text(
        self,
        response_text: str,
        question_text: str,
        response_data: list,
        serialized_rows: str,
        analysis_summary: str,
    ) -> str:
        """Replace empty or dump-like outputs with a readable paragraph summary."""
        cleaned_response = str(response_text or "").strip()

        if not cleaned_response or self._looks_like_raw_dump(cleaned_response, serialized_rows):
            return self._build_fallback_report(question_text, response_data, analysis_summary)

        if analysis_summary and not self._contains_analytical_signals(cleaned_response):
            return f"{cleaned_response}\n\n{analysis_summary}"

        return cleaned_response

    def _contains_analytical_signals(self, response_text: str) -> bool:
        """Check whether the model response already mentions analytical insights."""
        lowered = response_text.lower()
        signal_words = (
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
            "insight",
            "insights",
            "media",
            "moda",
            "outlier",
            "outliers",
            "tendencia",
            "tendencias",
        )
        return any(word in lowered for word in signal_words)

    def _looks_like_raw_dump(self, response_text: str, serialized_rows: str) -> bool:
        """Detect outputs that mostly echo raw rows instead of explaining them."""
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
        question_text: str,
        response_data: list,
        analysis_summary: str,
    ) -> str:
        """Create a simple paragraph report when the model returns a raw dump."""
        total_rows = len(response_data)
        first_row = response_data[0] if response_data and isinstance(response_data[0], dict) else {}
        columns = [str(key) for key in first_row.keys()]

        intro = (
            f"Com base nos dados retornados para a pergunta '{question_text}', "
            f"encontrei {total_rows} registro"
            f"{'' if total_rows == 1 else 's'}."
        )

        if columns:
            column_text = ", ".join(columns[:5])
            detail = (
                "Os principais campos disponiveis nesta consulta sao "
                f"{column_text}."
            )
        else:
            detail = (
                "A consulta retornou registros, mas sem campos suficientes para montar "
                "um detalhamento mais especifico."
            )

        example = self._build_example_paragraph(first_row, columns)

        return "\n\n".join(
            part for part in (intro, detail, analysis_summary, example) if part
        )

    def _build_example_paragraph(
        self,
        first_row: dict,
        columns: list[str],
    ) -> str:
        """Describe the first row as a readable example instead of dumping raw JSON."""
        if not first_row or not columns:
            return ""

        fragments = []
        for column in columns[:3]:
            value = first_row.get(column)
            fragments.append(f"{column}={value}")

        if not fragments:
            return ""

        values_text = ", ".join(fragments)
        return (
            "Como referencia, o primeiro registro mostra "
            f"{values_text}. Use esses dados como base para interpretar o resultado completo."
        )

    def _build_analysis_summary(self, response_data: list) -> str:
        """Build a deterministic analytical brief to guide the report."""
        rows = [row for row in response_data if isinstance(row, dict)]

        if not rows:
            return ""

        numeric_columns = self._extract_numeric_columns(rows)
        categorical_columns = self._extract_categorical_columns(rows, numeric_columns)
        paragraphs = []

        paragraphs.append(
            f"Destaques analiticos: a consulta retornou {len(rows)} registro"
            f"{'' if len(rows) == 1 else 's'}."
        )

        if numeric_columns:
            primary_metric = next(iter(numeric_columns))
            metric_values = numeric_columns[primary_metric]
            average_value = sum(metric_values) / len(metric_values)
            min_value = min(metric_values)
            max_value = max(metric_values)
            paragraphs.append(
                "Na metrica "
                f"{primary_metric}, a media e {self._format_number(average_value)}, "
                f"com minimo de {self._format_number(min_value)} e maximo de "
                f"{self._format_number(max_value)}."
            )

            metric_mode = self._describe_mode(metric_values)
            if metric_mode:
                paragraphs.append(
                    f"A moda numerica dessa metrica e {self._format_number(metric_mode)}."
                )
            else:
                paragraphs.append(
                    "Nao ha uma moda numerica clara para essa metrica, porque os valores "
                    "nao se repetem com frequencia relevante."
                )

            outlier_text = self._describe_outliers(primary_metric, metric_values)
            if outlier_text:
                paragraphs.append(outlier_text)

            trend_text = self._describe_trend(rows, primary_metric)
            if trend_text:
                paragraphs.append(trend_text)
            else:
                paragraphs.append(
                    "Nao foi possivel inferir uma tendencia confiavel com a ordenacao "
                    "disponivel nos dados."
                )
        else:
            paragraphs.append(
                "Nao ha metrica numerica suficiente para calcular media, outliers ou tendencia."
            )

        if categorical_columns:
            category_column = next(iter(categorical_columns))
            category_mode = self._describe_mode(categorical_columns[category_column])
            if category_mode is not None:
                frequency = categorical_columns[category_column].count(category_mode)
                paragraphs.append(
                    "Na dimensao "
                    f"{category_column}, a moda e '{category_mode}', aparecendo em "
                    f"{frequency} registro"
                    f"{'' if frequency == 1 else 's'}."
                )
        else:
            paragraphs.append(
                "Nao ha campo categorico suficiente para destacar a moda por frequencia."
            )

        return " ".join(paragraphs)

    def _extract_numeric_columns(self, rows: list[dict]) -> dict[str, list[float]]:
        """Return numeric columns with their numeric values."""
        values_by_column: dict[str, list[float]] = {}

        for row in rows:
            for key, value in row.items():
                if self._is_numeric(value):
                    values_by_column.setdefault(str(key), []).append(float(value))

        return {
            column: values
            for column, values in values_by_column.items()
            if values
        }

    def _extract_categorical_columns(
        self,
        rows: list[dict],
        numeric_columns: dict[str, list[float]],
    ) -> dict[str, list[str]]:
        """Return non-numeric columns with stringified values."""
        values_by_column: dict[str, list[str]] = {}

        for row in rows:
            for key, value in row.items():
                column = str(key)
                if column in numeric_columns:
                    continue

                if value is None:
                    continue

                values_by_column.setdefault(column, []).append(str(value))

        return {
            column: values
            for column, values in values_by_column.items()
            if values
        }

    def _is_numeric(self, value: object) -> bool:
        """Return True for plain numeric values."""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _describe_mode(self, values: list[object]) -> object:
        """Return the mode only when there is a repeated most-frequent value."""
        if not values:
            return None

        frequencies: dict[object, int] = {}
        for value in values:
            frequencies[value] = frequencies.get(value, 0) + 1

        best_value = max(frequencies, key=frequencies.get)
        if frequencies[best_value] <= 1:
            return None

        return best_value

    def _describe_outliers(self, column: str, values: list[float]) -> str:
        """Describe IQR outliers for a numeric metric when enough data exists."""
        if len(values) < 4:
            return (
                f"Nao ha dados suficientes em {column} para uma analise confiavel de outliers."
            )

        sorted_values = sorted(values)
        midpoint = len(sorted_values) // 2
        lower_half = sorted_values[:midpoint]
        upper_half = sorted_values[-midpoint:]
        q1 = self._median(lower_half)
        q3 = self._median(upper_half)
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        outliers = [
            value for value in sorted_values
            if value < lower_bound or value > upper_bound
        ]

        if not outliers:
            return (
                f"Nao surgiram outliers claros em {column} com base no intervalo interquartil."
            )

        preview = ", ".join(self._format_number(value) for value in outliers[:3])
        return (
            f"Foram identificados {len(outliers)} outlier"
            f"{'' if len(outliers) == 1 else 's'} em {column}; exemplos: {preview}."
        )

    def _describe_trend(self, rows: list[dict], metric_column: str) -> str:
        """Describe a simple trend for the primary numeric metric."""
        dated_rows = self._extract_dated_metric_series(rows, metric_column)
        if dated_rows:
            first_label, first_value = dated_rows[0]
            last_label, last_value = dated_rows[-1]
            trend_direction = self._trend_direction(first_value, last_value)
            return (
                f"A tendencia de {metric_column} e {trend_direction}, saindo de "
                f"{self._format_number(first_value)} em {first_label} para "
                f"{self._format_number(last_value)} em {last_label}."
            )

        ordered_values = [
            float(row[metric_column])
            for row in rows
            if metric_column in row and self._is_numeric(row[metric_column])
        ]
        if len(ordered_values) < 2:
            return ""

        first_value = ordered_values[0]
        last_value = ordered_values[-1]
        trend_direction = self._trend_direction(first_value, last_value)
        return (
            f"Considerando a ordem retornada pela consulta, a tendencia de {metric_column} "
            f"e {trend_direction}, indo de {self._format_number(first_value)} para "
            f"{self._format_number(last_value)}."
        )

    def _extract_dated_metric_series(
        self,
        rows: list[dict],
        metric_column: str,
    ) -> list[tuple[str, float]]:
        """Return metric values sorted by the first detected date-like column."""
        date_column = self._find_date_column(rows, metric_column)
        if not date_column:
            return []

        series: list[tuple[datetime, str, float]] = []
        for row in rows:
            raw_date = row.get(date_column)
            raw_metric = row.get(metric_column)
            if raw_date is None or not self._is_numeric(raw_metric):
                continue

            parsed_date = self._parse_datetime(raw_date)
            if parsed_date is None:
                continue

            series.append((parsed_date, str(raw_date), float(raw_metric)))

        series.sort(key=lambda item: item[0])
        return [(label, value) for _, label, value in series]

    def _find_date_column(self, rows: list[dict], metric_column: str) -> str:
        """Return the first date-like column different from the metric column."""
        for row in rows:
            for key, value in row.items():
                column = str(key)
                if column == metric_column or value is None:
                    continue

                if self._parse_datetime(value) is not None:
                    return column

        return ""

    def _parse_datetime(self, value: object) -> datetime | None:
        """Parse a limited set of date-like values."""
        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            return None

        candidate = value.strip()
        if not candidate:
            return None

        normalized = candidate.replace("Z", "+00:00")
        formats = (
            None,
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%m/%Y",
        )

        for date_format in formats:
            try:
                if date_format is None:
                    return datetime.fromisoformat(normalized)
                return datetime.strptime(normalized, date_format)
            except ValueError:
                continue

        return None

    def _trend_direction(self, first_value: float, last_value: float) -> str:
        """Return a qualitative trend direction."""
        if last_value > first_value:
            return "de alta"
        if last_value < first_value:
            return "de queda"
        return "estavel"

    def _median(self, values: list[float]) -> float:
        """Return the median for a sorted or unsorted numeric list."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        midpoint = len(sorted_values) // 2
        if len(sorted_values) % 2:
            return sorted_values[midpoint]

        return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2

    def _format_number(self, value: float | int) -> str:
        """Format numeric values compactly for prose."""
        numeric_value = float(value)
        if numeric_value.is_integer():
            return str(int(numeric_value))

        return f"{numeric_value:.2f}"
