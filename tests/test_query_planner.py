import unittest
import os
import sys

# Add the project root to the Python path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from query_planner import deconstruct_query


class TestQueryPlannerIntegration(unittest.TestCase):
    """
    Integration tests for the Query Planner.

    These tests make REAL API calls to the configured LLM (OpenRouter)
    to ensure the deconstruction logic works with a live model.
    """

    def test_deconstruct_query_produces_valid_plan(self):
        """
        Test that a standard query returns a valid, structured plan.
        """
        # Arrange
        user_query = "Find my notes on RAG that mention ChromaDB from last month."

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertIsInstance(plan, dict)
        self.assertIn("semantic_query", plan)
        self.assertIn("filters", plan)
        self.assertIn("response_format", plan)

        self.assertIsInstance(plan["semantic_query"], str)
        self.assertIsInstance(plan["filters"], list)
        self.assertIsInstance(plan["response_format"], str)
        self.assertTrue(plan["semantic_query"])  # Should not be empty

    def test_broad_query_selects_metadata_only_format(self):
        """
        Test that a broad, discovery-oriented query correctly selects the
        'metadata_only' response format.
        """
        # Arrange
        user_query = "What have I written about threat intelligence?"

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertEqual(plan["response_format"], "metadata_only")

    def test_specific_query_selects_selective_context_format(self):
        """
        Test that a specific, factual query correctly selects the
        'selective_context' response format.
        """
        # Arrange
        user_query = "What specific command did I use to transfer files with GfxDownloadWrapper.exe?"

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertEqual(plan["response_format"], "selective_context")

    def test_query_with_date_filter_is_parsed(self):
        """
        Test that the LLM correctly identifies and creates a date-based filter.
        """
        # Arrange
        user_query = "Show me notes about javascript created since yesterday."

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertTrue(
            any(f["field"] == "created_date" for f in plan["filters"]),
            "No created_date filter was found in the plan.",
        )


if __name__ == "__main__":
    # This allows running the tests directly
    # Ensure OPENROUTER_API_KEY is set in your environment
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)
    unittest.main()
