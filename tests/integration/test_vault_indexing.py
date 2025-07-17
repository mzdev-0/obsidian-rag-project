"""
Simple validation test for vault indexing functionality.

Tests the complete end-to-end workflow from vault directory to indexed documents
using the new RAGMicroAgent architecture.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from main import RAGMicroAgent


class TestVaultIndexing(unittest.TestCase):
    """Simple validation tests for vault indexing."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "qdrant_db"
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_basic_vault_indexing(self):
        """Test basic vault indexing with simple notes."""
        # Create test notes
        test_notes = {
            "test_note1.md": "# Test Note 1\nThis is a test note about RAG systems.",
            "test_note2.md": "# Test Note 2\nAnother test note with different content.",
        }
        
        for filename, content in test_notes.items():
            file_path = self.vault_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Test indexing
        agent = RAGMicroAgent()
        result = agent.index_vault(str(self.vault_path))
        
        # Validate results
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_found"], 2)
        self.assertEqual(result["files_processed"], 2)
        self.assertGreater(result["documents_added"], 0)
        self.assertEqual(len(result["errors"]), 0)

    def test_empty_vault_indexing(self):
        """Test indexing empty vault."""
        agent = RAGMicroAgent()
        result = agent.index_vault(str(self.vault_path))
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_found"], 0)
        self.assertEqual(result["files_processed"], 0)
        self.assertEqual(result["documents_added"], 0)

    def test_nested_directory_indexing(self):
        """Test indexing vault with nested directories."""
        # Create nested structure
        nested_dir = self.vault_path / "projects" / "2024"
        nested_dir.mkdir(parents=True)
        
        notes = {
            "root_note.md": "# Root Note\nContent",
            "projects/project_note.md": "# Project Note\nContent",
            "projects/2024/nested_note.md": "# Nested Note\nContent"
        }
        
        for rel_path, content in notes.items():
            file_path = self.vault_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        agent = RAGMicroAgent()
        result = agent.index_vault(str(self.vault_path))
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_found"], 3)
        self.assertEqual(result["files_processed"], 3)
        self.assertGreater(result["documents_added"], 0)

    def test_reset_collection_before_indexing(self):
        """Test indexing with reset flag."""
        # Create initial notes
        note_path = self.vault_path / "initial.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write("# Initial Note\nContent")
        
        agent = RAGMicroAgent()
        
        # First indexing
        result1 = agent.index_vault(str(self.vault_path))
        initial_count = result1["documents_added"]
        
        # Second indexing with reset
        result2 = agent.index_vault(str(self.vault_path), reset=True)
        
        self.assertEqual(result2["status"], "completed")
        self.assertEqual(result2["documents_added"], initial_count)

    def test_collection_stats_after_indexing(self):
        """Test collection statistics after indexing."""
        # Create test note
        note_path = self.vault_path / "stats_test.md"
        with open(note_path, "w", encoding="utf-8") as f:
            f.write("# Stats Test\nThis is a test note.")
        
        agent = RAGMicroAgent()
        agent.index_vault(str(self.vault_path))
        
        stats = agent.get_collection_stats()
        
        self.assertIn("document_count", stats)
        self.assertIn("collection_name", stats)
        self.assertIn("db_path", stats)
        self.assertGreater(stats["document_count"], 0)


if __name__ == "__main__":
    unittest.main()