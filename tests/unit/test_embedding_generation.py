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
import os
import tempfile
from pathlib import Path

from src.core.note import Note
from src.core.ingestion.processor import NoteProcessor, ProcessedDocument
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

        note = Note.from_file(str(sample_path))
        documents = list(self.processor.process_note(note))

        self.assertGreater(
            len(documents), 0, "Should generate at least one embedding document"
        )

        # Test embedding generation and document structure
        if self.embedder:
            test_content = documents[0].content
            embeddings = self.embedder.embed_documents([test_content])
            
            # Verify embedding structure
            self.assertIsInstance(embeddings, list, "Embedder should return a list")
            self.assertIsInstance(embeddings[0], list, "First element should be embedding vector")
            self.assertGreater(len(embeddings[0]), 100, "Embedding should have reasonable dimension")
            
            # Test embedding assignment to document
            doc = documents[0]
            doc.embedding = embeddings[0]
            self.assertIsNotNone(doc.embedding, "Document should have embedding assigned")
            self.assertIsInstance(doc.embedding, list, "Document embedding should be a list")
            self.assertGreater(len(doc.embedding), 100, "Document embedding should have reasonable dimension")

    def test_content_section_format(self):
        """Test embedding text format using new processor structure."""
        title = "RAG Systems"
        heading = "Hybrid Retrieval"
        content = "A hybrid approach combines semantic and keyword search"

        embedding_text = self.processor.create_embedding_text(title, heading, content)

        # Verify the correct format is used
        expected = f"{title} | {heading}\n\n{content}"
        self.assertEqual(embedding_text, expected)

    def test_chroma_document_format(self):
        """Test complete document structure for ChromaDB storage using new pipeline."""
        sample_path = self.sample_notes_dir / "sed.md"
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        documents = list(self.processor.process_file(str(sample_path)))
        self.assertGreater(len(documents), 0, "Should produce documents")

        # Verify complete document structure
        doc = documents[0]
        self.assertIsInstance(doc, ProcessedDocument)
        self.assertIsInstance(doc.id, str)
        self.assertGreater(len(doc.id), 0, "Document should have non-empty ID")
        self.assertIsInstance(doc.content, str)
        self.assertGreater(len(doc.content), 0, "Document should have content")
        self.assertIsInstance(doc.metadata, dict)
        
        # Verify required metadata fields
        required_fields = ["title", "file_path", "heading", "level", "tags", "wikilinks", "created_date", "modified_date"]
        for field in required_fields:
            self.assertIn(field, doc.metadata, f"Document metadata should contain '{field}'")
        
        # Verify embedding field exists and is initially None
        self.assertIsNone(doc.embedding, "Document embedding should initially be None")

    def test_real_sample_note_conversion(self):
        """Test with actual sample notes using new pipeline."""
        sample_path = self.sample_notes_dir / "2025 Threat Report - Huntress.md"
        self.assertTrue(sample_path.exists(), f"Sample note not found: {sample_path}")

        note = Note.from_file(str(sample_path))
        documents = list(self.processor.process_note(note))

        self.assertGreater(len(documents), 0, "Should produce at least one document")

        # Verify document structure and content integrity
        for doc in documents:
            self.assertIsInstance(doc, ProcessedDocument)
            self.assertIsInstance(doc.id, str)
            # Verify ID format - contains filename and numeric section index
            self.assertTrue("::" in doc.id, "Document ID should contain '::' separator")
            parts = doc.id.split("::")
            self.assertEqual(len(parts), 2, "Document ID should have exactly two parts")
            self.assertTrue(parts[1].isdigit(), "Second part should be numeric section index")
            self.assertIsInstance(doc.content, str)
            self.assertGreater(len(doc.content), 0, "Document should have non-empty content")
            self.assertIn(note.title, doc.content, "Document content should contain note title")
            self.assertIsInstance(doc.metadata, dict)
            
            # Verify metadata content
            self.assertEqual(doc.metadata["title"], note.title)
            self.assertEqual(doc.metadata["file_path"], str(note.file_path))
            self.assertIsInstance(doc.metadata["tags"], list)
            self.assertIsInstance(doc.metadata["wikilinks"], list)
            self.assertIsInstance(doc.metadata["created_date"], str)
            self.assertIsInstance(doc.metadata["modified_date"], str)
            
            # Verify embedding field is initially None
            self.assertIsNone(doc.embedding)


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

        # Verify complete document structure and workflow
        for doc in documents:
            self.assertIsInstance(doc, ProcessedDocument)
            self.assertIsInstance(doc.id, str)
            self.assertIsInstance(doc.content, str)
            self.assertGreater(len(doc.content), 0)
            self.assertIsInstance(doc.metadata, dict)
            
            # Verify all required metadata fields exist and have correct types
            metadata = doc.metadata
            self.assertIsInstance(metadata["title"], str)
            self.assertIsInstance(metadata["file_path"], str)
            self.assertIsInstance(metadata["heading"], str)
            self.assertIsInstance(metadata["level"], int)
            self.assertIsInstance(metadata["tags"], list)
            self.assertIsInstance(metadata["wikilinks"], list)
            self.assertIsInstance(metadata["created_date"], str)
            self.assertIsInstance(metadata["modified_date"], str)
            
            # Verify content format follows expected pattern
            expected_pattern = f"{metadata['title']} | {metadata['heading']}"
            self.assertTrue(doc.content.startswith(expected_pattern), 
                          f"Content should start with '{expected_pattern}'")
            
            # Verify embedding field is initially None
            self.assertIsNone(doc.embedding)

    def test_empty_note_handling(self):
        """Test processing of empty or minimal notes."""
        # Create a truly empty note file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
            self.assertEqual(len(documents), 1, "Should produce one document for note without headings")
            
            doc = documents[0]
            self.assertIsInstance(doc, ProcessedDocument)
            self.assertIsInstance(doc.id, str)
            # Verify ID format for notes without headings
            self.assertTrue("::" in doc.id, "Document ID should contain '::' separator")
            parts = doc.id.split("::")
            self.assertEqual(len(parts), 2, "Document ID should have exactly two parts")
            self.assertTrue(parts[1].isdigit(), "Second part should be numeric section index")
            self.assertIn("This is a note without any headings", doc.content)
            self.assertEqual(doc.metadata["heading"], "<No Heading>", "Heading should be '<No Heading>' for notes without sections")
            self.assertEqual(doc.metadata["level"], 0, "Level should be 0 for notes without sections")
            self.assertIsNone(doc.embedding)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
