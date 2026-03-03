from collections import Counter
from datetime import datetime
from typing import Any


ResponseRow = dict[str, Any]
NumericColumns = dict[str, list[float]]
CategoricalColumns = dict[str, list[str]]

DATE_PARSE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y",
)


class AnalyticalSummaryBuilder:
    """Build a deterministic analytical brief from query rows."""

    def build_summary(self, response_data: list[ResponseRow]) -> str:
        """Return a concise analytical summary grounded in the returned rows."""
        valid_rows = [row for row in response_data if isinstance(row, dict)]
        if not valid_rows:
            return ""

        numeric_columns = self._extract_numeric_columns(valid_rows)
        categorical_columns = self._extract_categorical_columns(
            valid_rows,
            numeric_columns,
        )

        paragraphs = [self._build_row_count_summary(valid_rows)]
        paragraphs.extend(self._build_numeric_summary(valid_rows, numeric_columns))

        categorical_summary = self._build_categorical_summary(categorical_columns)
        if categorical_summary:
            paragraphs.append(categorical_summary)

        return " ".join(paragraph for paragraph in paragraphs if paragraph)

    def _build_row_count_summary(self, rows: list[ResponseRow]) -> str:
        row_count = len(rows)
        return (
            f"Destaques analiticos: a consulta retornou {row_count} registro"
            f"{'' if row_count == 1 else 's'}."
        )

    def _build_numeric_summary(
        self,
        rows: list[ResponseRow],
        numeric_columns: NumericColumns,
    ) -> list[str]:
        if not numeric_columns:
            return [
                "Nao ha metrica numerica suficiente para calcular media, outliers ou tendencia."
            ]

        primary_metric = next(iter(numeric_columns))
        metric_values = numeric_columns[primary_metric]
        average_value = sum(metric_values) / len(metric_values)
        min_value = min(metric_values)
        max_value = max(metric_values)

        summary = [
            "Na metrica "
            f"{primary_metric}, a media e {self._format_number(average_value)}, "
            f"com minimo de {self._format_number(min_value)} e maximo de "
            f"{self._format_number(max_value)}.",
        ]

        metric_mode = self._describe_mode(metric_values)
        if metric_mode is None:
            summary.append(
                "Nao ha uma moda numerica clara para essa metrica, porque os valores "
                "nao se repetem com frequencia relevante."
            )
        else:
            summary.append(
                f"A moda numerica dessa metrica e {self._format_number(metric_mode)}."
            )

        summary.append(self._describe_outliers(primary_metric, metric_values))

        trend_text = self._describe_trend(rows, primary_metric)
        if trend_text:
            summary.append(trend_text)
        else:
            summary.append(
                "Nao foi possivel inferir uma tendencia confiavel com a ordenacao "
                "disponivel nos dados."
            )

        return summary

    def _build_categorical_summary(
        self,
        categorical_columns: CategoricalColumns,
    ) -> str:
        if not categorical_columns:
            return (
                "Nao ha campo categorico suficiente para destacar a moda por frequencia."
            )

        category_column = next(iter(categorical_columns))
        category_values = categorical_columns[category_column]
        category_mode = self._describe_mode(category_values)
        if category_mode is None:
            return ""

        frequency = category_values.count(category_mode)
        return (
            "Na dimensao "
            f"{category_column}, a moda e '{category_mode}', aparecendo em "
            f"{frequency} registro"
            f"{'' if frequency == 1 else 's'}."
        )

    def _extract_numeric_columns(self, rows: list[ResponseRow]) -> NumericColumns:
        values_by_column: NumericColumns = {}

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
        rows: list[ResponseRow],
        numeric_columns: NumericColumns,
    ) -> CategoricalColumns:
        values_by_column: CategoricalColumns = {}

        for row in rows:
            for key, value in row.items():
                column = str(key)
                if column in numeric_columns or value is None:
                    continue

                values_by_column.setdefault(column, []).append(str(value))

        return {
            column: values
            for column, values in values_by_column.items()
            if values
        }

    def _is_numeric(self, value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _describe_mode(self, values: list[object]) -> object:
        if not values:
            return None

        best_value, frequency = Counter(values).most_common(1)[0]
        if frequency <= 1:
            return None

        return best_value

    def _describe_outliers(self, column: str, values: list[float]) -> str:
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

    def _describe_trend(self, rows: list[ResponseRow], metric_column: str) -> str:
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
        rows: list[ResponseRow],
        metric_column: str,
    ) -> list[tuple[str, float]]:
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

    def _find_date_column(self, rows: list[ResponseRow], metric_column: str) -> str:
        for row in rows:
            for key, value in row.items():
                column = str(key)
                if column == metric_column or value is None:
                    continue

                if self._parse_datetime(value) is not None:
                    return column

        return ""

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            return None

        candidate = value.strip()
        if not candidate:
            return None

        normalized = candidate.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            pass

        for date_format in DATE_PARSE_FORMATS:
            try:
                return datetime.strptime(normalized, date_format)
            except ValueError:
                continue

        return None

    def _trend_direction(self, first_value: float, last_value: float) -> str:
        if last_value > first_value:
            return "de alta"
        if last_value < first_value:
            return "de queda"
        return "estavel"

    def _median(self, values: list[float]) -> float:
        if not values:
            return 0.0

        sorted_values = sorted(values)
        midpoint = len(sorted_values) // 2
        if len(sorted_values) % 2:
            return sorted_values[midpoint]

        return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2

    def _format_number(self, value: float | int) -> str:
        numeric_value = float(value)
        if numeric_value.is_integer():
            return str(int(numeric_value))

        return f"{numeric_value:.2f}"
