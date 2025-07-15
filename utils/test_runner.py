#!/usr/bin/env python3
"""
Test Runner for RAG Micro-Agent

This module contains the integration test logic that was previously in main.py,
refactored to use the new retriever interface.
"""

import unittest
import os
import sys
import glob
import shutil
import argparse
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LangChain and project-specific imports
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from note import Note
from embed import llama_embedder, create_embedding_text
from retriever import retrieve_context
from query_planner import deconstruct_query


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRetrieverIntegration(unittest.TestCase):
    """
    Integration tests for the Retriever module using the new interface.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a temporary ChromaDB database for testing.
        """
        cls.db_path = "./test_chroma_db_lc"
        cls.collection_name = "test_retriever_lc_collection"
        cls.note_files_path = "test_notes/*.md"

        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)

        note_files = glob.glob(cls.note_files_path)
        if not note_files:
            # Try alternative paths
            alt_paths = [
                "obsidian-rag-project/test_notes/*.md",
                "../test_notes/*.md",
                "./test_notes/*.md",
            ]
            for path in alt_paths:
                note_files = glob.glob(path)
                if note_files:
                    cls.note_files_path = path
                    break

            if not note_files:
                raise FileNotFoundError(
                    f"No test notes found. Checked paths: {alt_paths}"
                )

        # Prepare LangChain Document objects from source files
        langchain_docs = []
        cls.sections_per_note = {}
        for note_file in note_files:
            note = Note.from_file(note_file)
            cls.sections_per_note[note.title] = len(note.content_sections)
            for section in note.content_sections:
                embedding_text = create_embedding_text(
                    note.title, section.heading, section.content
                )
                metadata = {
                    "title": note.title,
                    "file_path": note.file_path,
                    "created_date": note.created_date.isoformat(),
                    "modified_date": note.modified_date.isoformat(),
                    "tags": ",".join(note.tag_wikilinks) if note.tag_wikilinks else "",
                    "wikilinks": ",".join(note.wikilinks) if note.wikilinks else "",
                    "heading": section.heading,
                    "level": section.level,
                }

                # Create a LangChain Document for each section
                doc = Document(page_content=embedding_text, metadata=metadata)
                langchain_docs.append(doc)

        # Create and populate the collection
        if langchain_docs:
            cls.vectorstore = Chroma.from_documents(
                documents=langchain_docs,
                embedding=llama_embedder,
                collection_name=cls.collection_name,
                persist_directory=cls.db_path,
            )

        # Get the raw chromadb collection object
        cls.collection = cls.vectorstore._collection

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary ChromaDB database after all tests."""
        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)

    def test_semantic_query_returns_relevant_context(self):
        """Test a conceptual query returns relevant, deduplicated results."""
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "How to evade detection?",
            "filters": [],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)
        self.assertGreater(len(context_package["results"]), 0)

        # Check that we got meaningful results
        titles = [r.get("title", "") for r in context_package["results"]]
        self.assertTrue(
            any("evasion" in t.lower() or "detection" in t.lower() for t in titles)
        )

    def test_metadata_filtering_works(self):
        """Test metadata filtering returns correct results."""
        query_plan = {
            "semantic_search_needed": False,
            "semantic_query": "",
            "filters": [
                {
                    "field": "title",
                    "operator": "$eq",
                    "value": "Evading Detection when Transferring Files",
                }
            ],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)
        self.assertGreater(len(context_package["results"]), 0)

        # All results should be from the specified note
        for result in context_package["results"]:
            self.assertEqual(
                result.get("title"), "Evading Detection when Transferring Files"
            )

    def test_metadata_only_format(self):
        """Test metadata_only response format."""
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "red team techniques",
            "filters": [],
            "response_format": "metadata_only",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)

        # Check format - should have metadata but no content
        for result in context_package["results"]:
            self.assertIn("id", result)
            self.assertIn("title", result)
            self.assertIn("heading", result)
            self.assertIn("tags", result)
            self.assertNotIn("content", result)

    def test_query_planner_integration(self):
        """Test integration with query planner."""
        user_query = "Show me notes about evasion techniques"

        # Use query planner to deconstruct
        query_plan = deconstruct_query(user_query)

        # Verify query plan structure
        self.assertIn("semantic_search_needed", query_plan)
        self.assertIn("semantic_query", query_plan)
        self.assertIn("filters", query_plan)
        self.assertIn("response_format", query_plan)

        # Execute with retriever
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)
        self.assertGreater(len(context_package["results"]), 0)

    def test_temporal_filtering(self):
        """Test temporal filtering with date ranges."""
        query_plan = {
            "semantic_search_needed": False,
            "semantic_query": "",
            "filters": [
                {
                    "field": "created_date",
                    "operator": "$gt",
                    "value": "2024-01-01T00:00:00",
                }
            ],
            "response_format": "metadata_only",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)

    def test_compound_filtering(self):
        """Test compound filters with multiple conditions."""
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "malware analysis",
            "filters": [
                {"field": "tags", "operator": "$contains", "value": "#redteam"},
                {"field": "level", "operator": "$gte", "value": 2},
            ],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)


def run_tests():
    """Run all integration tests."""
    # Configure test logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRetrieverIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    """CLI entry point for test runner."""
    parser = argparse.ArgumentParser(description="RAG Micro-Agent Test Runner")
    parser.add_argument(
        "--test-path",
        default="test_notes/*.md",
        help="Path pattern for test notes (default: test_notes/*.md)",
    )
    parser.add_argument(
        "--db-path",
        default="./test_chroma_db_lc",
        help="Path for temporary test database (default: ./test_chroma_db_lc)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("Running RAG Micro-Agent Integration Tests...")
    print("=" * 50)

    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
