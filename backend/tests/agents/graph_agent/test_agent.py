import unittest
from unittest.mock import Mock

from src.agents.graph_agent.agent import GraphAgent


class GraphAgentTests(unittest.TestCase):
    """Tests for graph suggestions and rendering."""

    def test_suggests_time_series_graphs_for_datetime_and_numeric_data(self) -> None:
        """It prioritizes a line chart when the x-axis looks date-like."""
        agent = GraphAgent()

        suggestions = agent.suggest_graphs(
            [
                {"month": "2026-01", "total": 10},
                {"month": "2026-02", "total": 20},
            ]
        )

        self.assertTrue(suggestions)
        self.assertEqual(suggestions[0]["id"], "line")
        self.assertEqual(suggestions[0]["x_field"], "month")
        self.assertEqual(suggestions[0]["y_field"], "total")

    def test_rejects_unknown_pattern_id(self) -> None:
        """It returns None when the requested pattern is not available for the data."""
        agent = GraphAgent()

        suggestion = agent.get_graph_pattern(
            [{"category": "Travel", "total": 10}],
            "pie",
        )

        self.assertIsNone(suggestion)

    def test_renders_png_graph_to_storage(self) -> None:
        """It renders the selected graph and returns the public storage path."""
        storage_manager = Mock()
        storage_manager.save_graph_image.return_value = "/v1/storage/graph/chat-1/question-1"
        agent = GraphAgent(storage_manager)
        graph_pattern = {
            "id": "bar_vertical",
            "label": "Bar",
            "reason": "Compares categories.",
            "x_field": "month",
            "y_field": "total",
            "hue_field": "",
        }

        graph_path = agent.render_graph(
            response_data=[
                {"month": "2026-01", "total": 10},
                {"month": "2026-02", "total": 20},
            ],
            graph_pattern=graph_pattern,
            user_email="user@example.com",
            chat_id="chat-1",
            question_id="question-1",
        )

        self.assertEqual(
            graph_path,
            "/v1/storage/graph/chat-1/question-1",
        )
        storage_manager.save_graph_image.assert_called_once()
