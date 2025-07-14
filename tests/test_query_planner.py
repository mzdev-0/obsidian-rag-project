import unittest
import os
import sys

# This allows the test runner to find the `query_planner` module
# in the parent directory. Uncomment if running this file directly.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from query_planner import deconstruct_query


class TestQueryPlannerIntegration(unittest.TestCase):
    """
    Integration tests for the Query Planner.

    These tests make REAL API calls to the configured LLM to ensure
    the deconstruction logic works as expected with a live model.
    The primary focus is validating the new `semantic_search_needed` flag
    and ensuring the overall plan structure is correct.
    """

    def test_deconstruct_query_produces_valid_plan_structure(self):
        """
        Test that a standard query returns a valid plan with all required keys and correct types.
        This is a fundamental smoke test.
        """
        # Arrange
        user_query = "Find my notes on RAG that mention ChromaDB from last month."

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        # Check for the presence of all top-level keys
        self.assertIn("semantic_search_needed", plan)
        self.assertIn("semantic_query", plan)
        self.assertIn("filters", plan)
        self.assertIn("response_format", plan)

        # Check that the types of the values are correct
        self.assertIsInstance(plan["semantic_search_needed"], bool)
        self.assertIsInstance(plan["semantic_query"], str)
        self.assertIsInstance(plan["filters"], list)
        self.assertIsInstance(plan["response_format"], str)

    def test_conceptual_query_needs_semantic_search(self):
        """
        Test that a conceptual query correctly sets `semantic_search_needed` to True
        and generates a non-empty semantic query string.
        """
        # Arrange
        user_query = "What are my thoughts on modern application state management?"

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertTrue(
            plan["semantic_search_needed"],
            "Conceptual query should require semantic search.",
        )
        self.assertTrue(
            plan["semantic_query"],
            "Semantic query should not be empty for a conceptual search.",
        )

    def test_metadata_query_does_not_need_semantic_search(self):
        """
        Test that a query based entirely on metadata correctly sets `semantic_search_needed` to False
        and provides an empty string for the semantic query.
        """
        # Arrange
        user_query = "List all files tagged with 'project-hydra'."

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertFalse(
            plan["semantic_search_needed"],
            "Metadata-only query should not require semantic search.",
        )
        self.assertEqual(
            plan["semantic_query"],
            "",
            "Semantic query should be empty for a metadata-only search.",
        )
        self.assertTrue(
            any(
                f["field"] == "tags" and f["value"] == ["project-hydra"]
                for f in plan["filters"]
            ),
            "The correct tag filter was not found in the plan.",
        )

    def test_broad_query_selects_metadata_only_format(self):
        """
        Test that a broad, discovery-oriented query correctly selects the 'metadata_only' response format.
        """
        # Arrange
        user_query = "What have I written about threat intelligence?"

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertEqual(plan["response_format"], "metadata_only")

    def test_specific_query_selects_selective_context_format(self):
        """
        Test that a specific, factual query correctly selects the 'selective_context' response format.
        """
        # Arrange
        user_query = (
            "Summarize my notes on the GfxDownloadWrapper.exe file transfer method."
        )

        # Act
        plan = deconstruct_query(user_query)

        # Assert
        self.assertEqual(plan["response_format"], "selective_context")

    def test_query_with_date_filter_is_parsed(self):
        """
        Test that the LLM correctly identifies and creates a date-based filter from natural language.
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
    # This allows running the tests directly from the command line
    # Ensure OPENROUTER_API_KEY is set in your environment before running.
    if not os.getenv("OPENROUTER_API_KEY"):
        print(
            "ERROR: The OPENROUTER_API_KEY environment variable is not set. Please set it to run the tests."
        )
        sys.exit(1)
    unittest.main()
