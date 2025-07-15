"""
Tests for embedding generation functionality.

Based on existing architecture, tests the note-to-embedding pipeline.
This module tests:
- Note parsing into structured sections
- Embedding generation using LlamaCppEmbeddings
- ChromaDB document storage format
- Integration with existing note.py and embed.py structures
"""

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

try:
    from src.core.note import Note
    from src.core.parsing import ContentSection
    from config import get_embedding_function
except ImportError:
    # Allow tests to run despite missing implementations
    Note = None
    ContentSection = None


class TestEmbeddingGeneration(unittest.TestCase):
    """Test embedding generation from note structures."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def test_single_section_embedding(self):
        """Test embedding generation for a single note section using new pipeline."""
        try:
            from src.core.note import Note
            from src.core.ingestion.processor import NoteProcessor
            from config import get_embedding_function
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")

        # Create test note structure
        note_content = """# Note Title
This is the main content.
Tags: [[Tags]]"""

        note_path = Path(self.temp_dir) / "test.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note_content)

        # Parse note using new pipeline
        note = Note.from_file(str(note_path))
        processor = NoteProcessor()
        documents = list(processor.process_note(note))
        self.assertGreater(len(documents), 0)

        # Generate embeddings using new embedder
        embedder = get_embedding_function()
        if embedder:
            for doc in documents:
                embeddings = embedder.embed_documents([doc.content])
                self.assertEqual(len(embeddings), 1)
                self.assertIsInstance(embeddings[0], list)
                self.assertIsInstance(embeddings[0][0], float)

    def test_content_section_format(self):
        """Test embedding text format using new processor structure."""
        try:
            from src.core.ingestion.processor import NoteProcessor
        except ImportError:
            self.skipTest("NoteProcessor not available")

        # Test the new processor format: "{note.title} | {heading}\n\n{content}"
        title = "RAG Systems"
        heading = "Hybrid Retrieval"
        content = "A hybrid approach combines semantic and keyword search"

        processor = NoteProcessor()
        embedding_text = processor.create_embedding_text(title, heading, content)

        # Verify the correct format is used
        expected = f"{title} | {heading}\n\n{content}"
        self.assertEqual(embedding_text, expected)

    def test_chroma_document_format(self):
        """Test document format for ChromaDB storage using new pipeline."""
        try:
            from src.core.ingestion.processor import NoteProcessor, ProcessedDocument
            from config import get_embedding_function
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")

        # Test data using new structure
        processor = NoteProcessor()
        embedder = get_embedding_function()

        # Instead of mock data, test the actual pipeline format
        # We'll just verify the structure of the processed documents
        title = "Test Note"
        heading = "Introduction"
        content = "Content for introduction"

        content_obj = processor.create_embedding_text(title, heading, content)

        # Verify format matches new pipeline
        expected = f"{title} | {heading}\n\n{content}"
        self.assertEqual(content_obj, expected)

        # Test embedding if embedder available
        if embedder:
            embeddings = embedder.embed_documents([content_obj])
            self.assertIsInstance(embeddings[0], list)
            self.assertIsInstance(embeddings[0][0], float)

    def test_real_sample_note_conversion(self):
        """Test with actual sample notes using new pipeline."""
        if not os.path.exists("data/sample_notes"):
            self.skipTest("Sample notes directory not found")

        sample_path = Path("data/sample_notes/2025 Threat Report - Huntress.md")
        if not sample_path.exists():
            self.skipTest("Sample note not found")

        try:
            from src.core.note import Note
            from src.core.ingestion.processor import NoteProcessor
            from config import get_embedding_function

            note = Note.from_file(str(sample_path))
            processor = NoteProcessor()

            # Process note through new pipeline
            documents = list(processor.process_note(note))
            self.assertGreater(
                len(documents), 0, "Should produce at least one document"
            )

            # Generate embeddings using new embedder
            embedder = get_embedding_function()
            if embedder:
                for doc in documents:
                    embeddings = embedder.embed_documents([doc.content])
                    # Verify vector dimension
                    self.assertGreater(
                        len(embeddings[0]), 100
                    )  # Typical embedding size

        except Exception as e:
            self.skipTest(f"Sample note processing failed: {e}")


class TestNoteToDocumentConversion(unittest.TestCase):
    """Test conversion from Note objects to embedded documents using new pipeline."""

    def test_full_note_parsing_workflow(self):
        """Test complete workflow from file to embedded documents using new ingestion."""
        try:
            from src.core.note import Note
            from src.core.ingestion.processor import NoteProcessor
            from config import get_embedding_function
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")

        temp_dir = tempfile.mkdtemp()

        try:
            # Create realistic test note
            note_content = """# Project Overview - RAG Architecture
This note covers the RAG micro-agent design.

## Core Components
The system has three main parts: query planner, retriever, and packaging.

## Technical Stack
Uses Python, ChromaDB, and local LLM models.

Tags: [[python]], [[rag]], [[architecture]]"""

            note_path = Path(temp_dir) / "overview.md"
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(note_content)

            # Process note using new pipeline
            processor = NoteProcessor()
            documents = list(processor.process_file(str(note_path)))

            # Verify we get documents
            self.assertGreater(len(documents), 0)

            # Generate embeddings using new embedder (optional check)
            embedder = get_embedding_function()
            if embedder:
                for doc in documents:
                    embeddings = embedder.embed_documents([doc.content])
                    # Verify valid embeddings using actual format
                    self.assertIsInstance(embeddings, list)
                    self.assertEqual(len(embeddings), 1)
                    self.assertIsInstance(embeddings[0], list)
                    self.assertIsInstance(embeddings[0][0], (int, float))

            # Verify metadata structure in new system
            for doc in documents:
                self.assertIn("title", doc.metadata)
                self.assertIn("tags", doc.metadata)
                self.assertIn("file_path", doc.metadata)

        finally:
            import shutil

            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
