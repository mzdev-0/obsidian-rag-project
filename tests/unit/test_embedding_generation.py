"""
Tests for embedding generation functionality.

Based on existing architecture, tests the note-to-embedding pipeline.
This module tests:
- Note parsing into structured sections
- Embedding generation using LlamaCppEmbeddings
- Qdrant document storage format
- Integration with existing note.py and embed.py structures
"""

import unittest
import os
import tempfile
from pathlib import Path

from langchain.schema import Document
from src.core.note import Note
from src.core.ingestion.processor import NoteProcessor
from config import get_embedding_function


class TestEmbeddingGeneration(unittest.TestCase):
    """Test embedding generation from note structures."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_notes_dir = Path("data/sample_notes")
        self.processor = NoteProcessor()
        self.embedder = get_embedding_function()

    def test_single_section_embedding(self):
        """Test embedding generation using sample note with single heading."""
        sample_path = self.sample_notes_dir / "sed.md"
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        note = Note.from_file(sample_path)

        documents = list(self.processor.process_note(note))

        self.assertGreater(
            len(documents), 0, "Should generate at least one embedding document"
        )

        # Test embedding generation using LangChain Document structure
        if self.embedder:
            test_content = documents[0].page_content
            embeddings = self.embedder.embed_documents([test_content])

            # Verify embedding structure
            self.assertIsInstance(embeddings, list, "Embedder should return a list")
            self.assertIsInstance(
                embeddings[0], list, "First element should be embedding vector"
            )
            self.assertGreater(
                len(embeddings[0]), 100, "Embedding should have reasonable dimension"
            )

    def test_qdrant_document_format(self):
        """Test complete document structure for Qdrant storage using new pipeline."""
        sample_path = self.sample_notes_dir / "sed.md"
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        documents = list(self.processor.process_file(str(sample_path)))
        self.assertGreater(len(documents), 0, "Should produce documents")

        # Verify complete document structure (LangChain Document)
        doc = documents[0]
        self.assertIsInstance(doc.page_content, str)
        self.assertGreater(len(doc.page_content), 0, "Document should have content")
        self.assertIsInstance(doc.metadata, dict)

        # Verify required metadata fields
        required_fields = [
            "title",
            "file_path",
            "heading",
            "level",
            "tags",
            "wikilinks",
            "created_date",
            "modified_date",
            "section_id",
        ]
        for field in required_fields:
            self.assertIn(
                field, doc.metadata, f"Document metadata should contain '{field}'"
            )

        # Verify metadata field types for Qdrant
        metadata = doc.metadata
        self.assertIsInstance(metadata["title"], str)
        self.assertIsInstance(metadata["file_path"], str)
        self.assertIsInstance(metadata["heading"], str)
        self.assertIsInstance(metadata["level"], int)
        self.assertIsInstance(metadata["tags"], list)
        self.assertIsInstance(metadata["wikilinks"], list)
        self.assertIsInstance(metadata["created_date"], int)  # Unix timestamp
        self.assertIsInstance(metadata["modified_date"], int)  # Unix timestamp
        self.assertIsInstance(metadata["section_id"], str)

    def test_real_sample_note_conversion(self):
        """Test with actual sample notes using new pipeline."""
        sample_path = self.sample_notes_dir / "2025 Threat Report - Huntress.md"
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        note = Note.from_file(str(sample_path))
        documents = list(self.processor.process_note(note))

        self.assertGreater(len(documents), 0, "Should produce at least one document")

        # Verify document structure and content integrity (LangChain Document)
        for doc in documents:
            self.assertIsInstance(doc.page_content, str)
            self.assertGreater(
                len(doc.page_content), 0, "Document should have non-empty content"
            )
            self.assertIsInstance(doc.metadata, dict)

            # Verify metadata content
            metadata = doc.metadata
            self.assertEqual(metadata["title"], note.title)
            self.assertEqual(metadata["file_path"], str(note.file_path))
            self.assertIsInstance(metadata["tags"], list)
            self.assertIsInstance(metadata["wikilinks"], list)
            self.assertIsInstance(metadata["created_date"], int)  # Unix timestamp
            self.assertIsInstance(metadata["modified_date"], int)  # Unix timestamp
            self.assertIsInstance(metadata["section_id"], str)

            # Verify content format follows expected pattern
            expected_pattern = f"{metadata['title']} | {metadata['heading']}"
            self.assertTrue(
                doc.page_content.startswith(expected_pattern),
                f"Content should start with '{expected_pattern}'",
            )


class TestNoteToDocumentConversion(unittest.TestCase):
    """Test conversion from Note objects to embedded documents using new pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_notes_dir = Path("data/sample_notes")
        self.processor = NoteProcessor()

    def test_full_note_parsing_workflow(self):
        """Test complete workflow using actual sample note with multiple sections."""
        sample_path = (
            self.sample_notes_dir / "Downloading and Uploading Files in Powershell.md"
        )
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        documents = list(self.processor.process_file(str(sample_path)))
        self.assertGreater(len(documents), 0, "Should produce at least one document")

        # Verify complete document structure and workflow (LangChain Document)
        for doc in documents:
            self.assertIsInstance(doc.page_content, str)
            self.assertGreater(len(doc.page_content), 0)
            self.assertIsInstance(doc.metadata, dict)

            # Verify all required metadata fields exist and have correct types
            metadata = doc.metadata
            self.assertIsInstance(metadata["title"], str)
            self.assertIsInstance(metadata["file_path"], str)
            self.assertIsInstance(metadata["heading"], str)
            self.assertIsInstance(metadata["level"], int)
            self.assertIsInstance(metadata["tags"], list)
            self.assertIsInstance(metadata["wikilinks"], list)
            self.assertIsInstance(metadata["created_date"], int)  # Unix timestamp
            self.assertIsInstance(metadata["modified_date"], int)  # Unix timestamp
            self.assertIsInstance(metadata["section_id"], str)

            # Verify content format follows expected pattern
            expected_pattern = f"{metadata['title']} | {metadata['heading']}"
            self.assertTrue(
                doc.page_content.startswith(expected_pattern),
                f"Content should start with '{expected_pattern}'",
            )

    def test_empty_note_handling(self):
        """Test processing of empty or minimal notes."""
        # Create a truly empty note file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Empty Note\n\n")
            temp_path = f.name

        try:
            documents = list(self.processor.process_file(temp_path))
            # Empty content should produce 0 documents
            self.assertEqual(len(documents), 0)
        finally:
            os.unlink(temp_path)

    def test_note_without_headings(self):
        """Test processing notes without markdown headings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("This is a note without any headings\nJust plain content here.")
            temp_path = f.name

        try:
            documents = list(self.processor.process_file(temp_path))
            self.assertEqual(
                len(documents),
                1,
                "Should produce one document for note without headings",
            )

            doc = documents[0]
            self.assertIsInstance(doc.page_content, str)
            self.assertIn("This is a note without any headings", doc.page_content)

            metadata = doc.metadata
            self.assertEqual(
                metadata["heading"],
                "<No Heading>",
                "Heading should be '<No Heading>' for notes without sections",
            )
            self.assertEqual(
                metadata["level"], 0, "Level should be 0 for notes without sections"
            )
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
