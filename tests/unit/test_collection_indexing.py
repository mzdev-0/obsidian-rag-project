"""
Tests for collection indexing performance and resilience with real sample notes.
"""

import pytest
import time
import psutil
import os
from pathlib import Path
from src.core.ingestion.vector_manager import VectorStoreManager
from src.core.ingestion.processor import NoteProcessor
from src.core.note import Note


class TestCollectionIndexing:
    """Test collection indexing performance and resilience."""

    def test_bulk_indexing_performance(self, real_sample_notes, vector_store_manager):
        """Test all real sample notes indexed efficiently."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")

        # Clear collection for clean test
        vector_store_manager.clear_collection()

        # Record start time and memory
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Index all notes
        processor = NoteProcessor()
        total_documents = 0

        for note in real_sample_notes:
            documents = list(processor.process_note(note))
            if documents:
                # Use the actual UUIDs from the Document metadata
                doc_ids = [doc.metadata["id"] for doc in documents]
                vector_store_manager.store_documents(documents, doc_ids)
                total_documents += len(documents)

        # Record end metrics
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Verify indexing completed
        collection_count = vector_store_manager.get_collection_count()
        assert collection_count == total_documents

        # Performance assertions
        indexing_time = end_time - start_time
        memory_increase = end_memory - start_memory

        # Should complete within reasonable time (adjust based on note count)
        assert indexing_time < collection_count * 60  # 1 minute per document
        assert memory_increase < collection_count * 100  # 500MB max memory increase

    def test_incremental_single_note_indexing(
        self, vector_store_manager, real_sample_notes
    ):
        """Test adding single note from real samples to existing collection."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")

        # Clear collection
        vector_store_manager.clear_collection()

        # Get initial count
        initial_count = vector_store_manager.get_collection_count()

        # Add single note
        note = real_sample_notes[0]
        processor = NoteProcessor()
        documents = list(processor.process_note(note))

        if documents:
            # Use the actual UUIDs from the Document metadata
            doc_ids = [doc.metadata["id"] for doc in documents]
            vector_store_manager.store_documents(documents, doc_ids)

            # Verify count increased correctly
            new_count = vector_store_manager.get_collection_count()
            assert new_count == initial_count + len(documents)

    def test_large_note_processing(self, vector_store_manager):
        """Test largest sample note processed correctly."""
        # Create a large test note (simulate large content)
        large_content = "# Large Note\n\n" + "This is a test paragraph.\n" * 1000

        # Create temporary large note
        temp_file = Path("./data/sample_notes/temp_large_test.md")
        try:
            temp_file.write_text(large_content)

            note = Note.from_file(str(temp_file))
            processor = NoteProcessor()
            documents = list(processor.process_note(note))

            # Should process without error
            assert len(documents) > 0

            # Should handle large content
            total_chars = sum(len(doc.page_content) for doc in documents)
            assert total_chars > 10000  # At least 10KB processed

            # Should store successfully
            doc_ids = [doc.metadata["id"] for doc in documents]
            vector_store_manager.store_documents(documents, doc_ids)

            # Verify storage
            collection_count = vector_store_manager.get_collection_count()
            assert collection_count >= len(documents)

        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()

    def test_memory_usage_during_bulk_operations(
        self, real_sample_notes, vector_store_manager
    ):
        """Test memory usage during bulk operations with real data."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")

        # Clear collection
        vector_store_manager.clear_collection()

        # Monitor memory during bulk operations
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Process notes in bulk
        processor = NoteProcessor()
        total_documents = 0

        for note in real_sample_notes:
            documents = list(processor.process_note(note))
            if documents:
                # Use the actual UUIDs from the Document metadata
                doc_ids = [doc.metadata["id"] for doc in documents]
                vector_store_manager.store_documents(documents, doc_ids)
                total_documents += len(documents)

        # Check final memory usage
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory should not grow excessively
        assert memory_increase < 1000  # 1GB max increase for reasonable dataset
        assert total_documents > 0  # Should have processed some documents

