from __future__ import annotations

from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.infra.logging_utils import LoggedComponent


PRIMARY_COLOR = "#009EFB"
SECONDARY_COLOR = "#006B99"
BACKGROUND_COLOR = "#FFFFFF"


class GraphAgent(LoggedComponent):
    """Build graph suggestions and render selected graphs."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        super().__init__()
        self._storage_dir = storage_dir
        sns.set_theme(style="whitegrid")

    def suggest_graphs(self, response_data: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Return deterministic graph suggestions for the given response rows."""
        dataframe = self._build_dataframe(response_data)
        if dataframe is None:
            return []

        numeric_columns = self._numeric_columns(dataframe)
        datetime_columns = self._datetime_columns(dataframe)
        categorical_columns = self._categorical_columns(
            dataframe,
            numeric_columns=numeric_columns,
            datetime_columns=datetime_columns,
        )

        suggestions: list[dict[str, str]] = []

        if datetime_columns and numeric_columns:
            x_field = datetime_columns[0]
            y_field = numeric_columns[0]
            suggestions.append(
                self._build_suggestion(
                    graph_id="line",
                    label="Line",
                    reason="Shows how the metric changes over time.",
                    x_field=x_field,
                    y_field=y_field,
                )
            )
            suggestions.append(
                self._build_suggestion(
                    graph_id="bar_vertical",
                    label="Bar",
                    reason="Compares the metric across each time bucket.",
                    x_field=x_field,
                    y_field=y_field,
                )
            )

        if categorical_columns and numeric_columns:
            x_field = categorical_columns[0]
            y_field = numeric_columns[0]
            suggestions.append(
                self._build_suggestion(
                    graph_id="bar_vertical",
                    label="Bar",
                    reason="Compares values across categories.",
                    x_field=x_field,
                    y_field=y_field,
                )
            )
            if len(dataframe.index) > 5:
                suggestions.append(
                    self._build_suggestion(
                        graph_id="bar_horizontal",
                        label="Horizontal Bar",
                        reason="Makes larger category lists easier to read.",
                        x_field=x_field,
                        y_field=y_field,
                    )
                )

        if len(numeric_columns) >= 2:
            suggestions.append(
                self._build_suggestion(
                    graph_id="scatter",
                    label="Scatter",
                    reason="Highlights correlation between two numeric fields.",
                    x_field=numeric_columns[0],
                    y_field=numeric_columns[1],
                )
            )

        if len(numeric_columns) == 1:
            suggestions.append(
                self._build_suggestion(
                    graph_id="histogram",
                    label="Histogram",
                    reason="Shows the value distribution for the metric.",
                    x_field=numeric_columns[0],
                )
            )

        return self._deduplicate_suggestions(suggestions)[:3]

    def get_graph_pattern(
        self,
        response_data: list[dict[str, Any]],
        graph_pattern_id: str,
    ) -> Optional[dict[str, str]]:
        """Return the selected graph suggestion when it is valid for the data."""
        normalized_pattern_id = str(graph_pattern_id).strip()
        for suggestion in self.suggest_graphs(response_data):
            if suggestion["id"] == normalized_pattern_id:
                return suggestion
        return None

    def render_graph(
        self,
        response_data: list[dict[str, Any]],
        graph_pattern: dict[str, str],
        chat_id: str,
        question_id: str,
    ) -> str:
        """Render the selected graph and return the public storage path."""
        if self._storage_dir is None:
            raise RuntimeError("GraphAgent requires a storage directory to render files.")

        dataframe = self._build_dataframe(response_data)
        if dataframe is None:
            raise ValueError("Graph rendering requires non-empty tabular data.")

        graph_id = graph_pattern["id"]
        x_field = graph_pattern["x_field"]
        y_field = graph_pattern["y_field"]
        hue_field = graph_pattern["hue_field"] or None

        figure, axis = plt.subplots(figsize=(8, 4.8), facecolor=BACKGROUND_COLOR)
        axis.set_facecolor(BACKGROUND_COLOR)

        palette = [PRIMARY_COLOR, SECONDARY_COLOR]
        if graph_id == "bar_vertical":
            sns.barplot(
                data=dataframe,
                x=x_field,
                y=y_field,
                hue=hue_field,
                ax=axis,
                palette=palette if hue_field else None,
                color=PRIMARY_COLOR if not hue_field else None,
            )
        elif graph_id == "bar_horizontal":
            sns.barplot(
                data=dataframe,
                x=y_field,
                y=x_field,
                hue=hue_field,
                ax=axis,
                palette=palette if hue_field else None,
                color=PRIMARY_COLOR if not hue_field else None,
                orient="h",
            )
        elif graph_id == "line":
            plot_frame = dataframe.sort_values(by=x_field)
            sns.lineplot(
                data=plot_frame,
                x=x_field,
                y=y_field,
                hue=hue_field,
                ax=axis,
                palette=palette if hue_field else None,
                color=PRIMARY_COLOR if not hue_field else None,
            )
        elif graph_id == "scatter":
            sns.scatterplot(
                data=dataframe,
                x=x_field,
                y=y_field,
                hue=hue_field,
                ax=axis,
                palette=palette if hue_field else None,
                color=PRIMARY_COLOR if not hue_field else None,
            )
        elif graph_id == "histogram":
            sns.histplot(
                data=dataframe,
                x=x_field,
                ax=axis,
                color=PRIMARY_COLOR,
            )
        else:
            plt.close(figure)
            raise ValueError(f"Unsupported graph pattern: {graph_id}")

        axis.tick_params(colors=SECONDARY_COLOR)
        axis.xaxis.label.set_color(SECONDARY_COLOR)
        axis.yaxis.label.set_color(SECONDARY_COLOR)
        axis.title.set_color(SECONDARY_COLOR)
        legend = axis.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(BACKGROUND_COLOR)

        figure.tight_layout()

        target_dir = self._storage_dir / chat_id / "graphics" / question_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "graph.png"
        figure.savefig(
            file_path,
            format="png",
            facecolor=figure.get_facecolor(),
            bbox_inches="tight",
        )
        plt.close(figure)

        return f"/storage/{chat_id}/graphics/{question_id}/{file_path.name}"

    def _build_dataframe(
        self,
        response_data: list[dict[str, Any]],
    ) -> Optional[pd.DataFrame]:
        """Convert response rows into a clean dataframe when possible."""
        if not response_data:
            return None

        dataframe = pd.DataFrame(response_data)
        if dataframe.empty:
            return None

        dataframe = dataframe.copy()
        dataframe = dataframe.dropna(axis=1, how="all")
        if dataframe.empty:
            return None

        for column in list(dataframe.columns):
            series = dataframe[column]
            if self._looks_datetime(series):
                dataframe[column] = pd.to_datetime(series, errors="coerce")
                continue

            if self._looks_numeric(series):
                dataframe[column] = pd.to_numeric(series, errors="coerce")

        return dataframe

    def _numeric_columns(self, dataframe: pd.DataFrame) -> list[str]:
        """Return numeric columns excluding booleans."""
        numeric_columns: list[str] = []
        for column in dataframe.columns:
            series = dataframe[column]
            if pd.api.types.is_bool_dtype(series):
                continue
            if pd.api.types.is_numeric_dtype(series):
                numeric_columns.append(str(column))
        return numeric_columns

    def _datetime_columns(self, dataframe: pd.DataFrame) -> list[str]:
        """Return columns that were normalized as datetimes."""
        columns: list[str] = []
        for column in dataframe.columns:
            if pd.api.types.is_datetime64_any_dtype(dataframe[column]):
                columns.append(str(column))
        return columns

    def _categorical_columns(
        self,
        dataframe: pd.DataFrame,
        *,
        numeric_columns: list[str],
        datetime_columns: list[str],
    ) -> list[str]:
        """Return non-numeric, non-datetime columns that still carry data."""
        excluded_columns = set(numeric_columns) | set(datetime_columns)
        columns: list[str] = []
        for column in dataframe.columns:
            column_name = str(column)
            if column_name in excluded_columns:
                continue
            if dataframe[column].dropna().empty:
                continue
            columns.append(column_name)
        return columns

    def _looks_numeric(self, series: pd.Series) -> bool:
        """Return True when the series can reasonably be treated as numeric."""
        non_null_values = series.dropna()
        if non_null_values.empty:
            return False

        if pd.api.types.is_numeric_dtype(non_null_values):
            return True

        converted_values = pd.to_numeric(non_null_values, errors="coerce")
        successful_values = converted_values.notna().sum()
        return successful_values == len(non_null_values)

    def _looks_datetime(self, series: pd.Series) -> bool:
        """Return True when the series can reasonably be treated as datetime."""
        non_null_values = series.dropna()
        if non_null_values.empty:
            return False

        if pd.api.types.is_datetime64_any_dtype(non_null_values):
            return True

        if pd.api.types.is_numeric_dtype(non_null_values):
            return False

        sample_values = list(non_null_values.head(10))
        if not sample_values:
            return False

        if all(isinstance(value, (date, datetime, pd.Timestamp)) for value in sample_values):
            return True

        converted_values = pd.to_datetime(sample_values, errors="coerce")
        successful_values = pd.Series(converted_values).notna().sum()
        return successful_values == len(sample_values)

    def _build_suggestion(
        self,
        *,
        graph_id: str,
        label: str,
        reason: str,
        x_field: str,
        y_field: str = "",
        hue_field: str = "",
    ) -> dict[str, str]:
        """Return a serializable graph suggestion object."""
        return {
            "id": graph_id,
            "label": label,
            "reason": reason,
            "x_field": x_field,
            "y_field": y_field,
            "hue_field": hue_field,
        }

    def _deduplicate_suggestions(
        self,
        suggestions: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """Keep only the first suggestion for each graph id."""
        seen_ids: set[str] = set()
        unique_suggestions: list[dict[str, str]] = []
        for suggestion in suggestions:
            graph_id = suggestion["id"]
            if graph_id in seen_ids:
                continue

            unique_suggestions.append(suggestion)
            seen_ids.add(graph_id)

        return unique_suggestions
