"""
Tests for Qdrant query execution using real sample notes.
"""

import pytest
from src.core.ingestion.vector_manager import VectorStoreManager
from src.core.ingestion.processor import NoteProcessor
from src.core.query_planner import deconstruct_query
from src.core.retriever import retrieve_context


class TestQdrantQueryExecution:
    """Test Qdrant query execution with real sample data."""

    def test_semantic_search_with_filters(
        self, vector_store_manager, real_sample_notes
    ):
        """Test vector search + payload filtering returns correct results from real sample data."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")

        processor = NoteProcessor()
        note = real_sample_notes[0]
        documents = processor.process_note(note)
        for i in documents:
            document = next(documents)
            doc_content = document.page_content
            doc_metadata = document.metadata
            vector_store_manager.store_document(doc_content, doc_metadata)

        # Create query plan with semantic search + filters
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "info on infostealers",
            "filters": [],
            "response_format": "selective_context",
        }

        # Execute query
        result = retrieve_context(query_plan, vector_store_manager)
        print("----------Result------------\n")
        print(result)

        # Verify results
        assert "results" in result
        assert isinstance(result["results"], list)

        # Should return some results if notes contain security content
        if len(result["results"]) > 0:
            for doc in result["results"]:
                assert "content" in doc
                assert "metadata" in doc
                assert "title" in doc["metadata"]

    # def test_metadata_only_retrieval(self, vector_store_manager, real_sample_notes):
    #    """Test search using only payload filters (no semantic search)."""
    #    if not real_sample_notes:
    #        pytest.skip("No sample notes available")

    #    # Index a single note
    #    processor = NoteProcessor()
    #    note = real_sample_notes[0]
    #    documents = processor.process_note(note)
    #    for i in documents:
    #        document = next(documents)
    #        doc_content = document.page_content
    #        doc_metadata = document.metadata
    #        vector_store_manager.store_document(doc_content, doc_metadata)

    #    # Create query plan with metadata-only search
    #    query_plan = {
    #        "semantic_search_needed": False,
    #        "semantic_query": "",
    #        "filters": [
    #            {"field": "created_date", "operator": "gte", "value": 1704067200}
    #        ],
    #        "response_format": "metadata_only",
    #    }

    #    # Execute query
    #    result = retrieve_context(query_plan, vector_store_manager)

    #    # Verify results
    #    assert "results" in result
    #    assert isinstance(result["results"], list)

    #    # Should return metadata-only format
    #    if len(result["results"]) > 0:
    #        for doc in result["results"]:
    #            assert "title" in doc
    #            assert "heading" in doc
    #            assert "tags" in doc
    #            assert "content" not in doc  # metadata_only format

    def test_empty_results_handling(self, vector_store_manager):
        """Test graceful handling when no documents match criteria."""
        # Create query plan that should return no results
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "nonexistent_topic_xyz_123",
            "filters": [
                {"field": "created_date", "operator": "gte", "value": 9999999999}
            ],
            "response_format": "selective_context",
        }

        # Execute query
        result = retrieve_context(query_plan, vector_store_manager)

        # Verify empty results handling
        assert "results" in result
        assert isinstance(result["results"], list)
        assert len(result["results"]) == 0
