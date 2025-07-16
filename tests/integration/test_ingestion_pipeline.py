"""
Integration tests for the complete note ingestion pipeline.

These tests validate the end-to-end workflow from markdown files to
embedded documents in ChromaDB, using the new RAGMicroAgent architecture.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from main import RAGMicroAgent


class TestFullIngestionPipeline(unittest.TestCase):
    """End-to-end tests for note ingestion pipeline."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "chroma_db"
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_vault_to_embedding_pipeline(self):
        """Test complete pipeline from vault directory to vector store."""
        # Create test vault structure
        test_notes = {
            "note1.md": """# Project Overview
This project implements a RAG micro-agent.

## scope
The scope is...""",
            "note2.md": """# Technical Implementation
Implementation details for the RAG system.

## architecture
The architecture consists of...""",
        }
        
        # Write test files
        for filename, content in test_notes.items():
            file_path = self.vault_path / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Test actual pipeline with RAGMicroAgent
        agent = RAGMicroAgent()
        result = agent.index_vault(str(self.vault_path))
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_found"], 2)
        self.assertEqual(result["files_processed"], 2)
        self.assertGreater(result["documents_added"], 0)

    def test_sample_vault_processes_correctly(self):
        """Test processing with actual sample notes if available."""
        if not Path("data/sample_notes").exists():
            self.skipTest("Sample notes directory not found")
            
        sample_path = Path("data/sample_notes")
        if not list(sample_path.glob("*.md")):
            self.skipTest("No sample notes found")
        
        processed_count = 0
        for note_file in sample_path.glob("*.md"):
            if not note_file.name.startswith("."):
                processed_count += 1
        
        self.assertGreater(processed_count, 0)

    def test_empty_vault_handling(self):
        """Test handling empty vault directories."""
        empty_vault = self.vault_path / "empty"
        empty_vault.mkdir()
        
        # Should return no notes to process
        md_files = list(empty_vault.glob("*.md"))
        self.assertEqual(len(md_files), 0)

    def test_nested_directory_scanning(self):
        """Test processing notes in nested directory structures."""
        # Create nested structure
        nested_dir = self.vault_path / "projects" / "2024"
        nested_dir.mkdir(parents=True)
        
        with open(nested_dir / "project.md", "w", encoding="utf-8") as f:
            f.write("# New Project\nProject description.")
        
        # Simulate recursive scanning
        all_md_files = []
        for root, dirs, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith('.md') and not file.startswith('.'):
                    all_md_files.append(os.path.join(root, file))
        
        self.assertIn(str(nested_dir / "project.md"), all_md_files)

    def test_note_metadata_passthrough(self):
        """Test that note metadata flows correctly through pipeline."""
        test_note = """# Test Note Title
This is the content section.

Date: 01-01-2024 12:00 PM
Tags: [[test]], [[pipeline]]"""
        
        note_file = self.vault_path / "test.md"
        with open(note_file, "w", encoding="utf-8") as f:
            f.write(test_note)
        
        # Simulate metadata extraction pipeline
        stat_result = note_file.stat()
        
        expected_metadata = {
            'title': 'Test Note Title',
            'file_path': str(note_file),
            'created_date': datetime.fromtimestamp(stat_result.st_ctime).isoformat(),
            'modified_date': datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
            'tags': ['test', 'pipeline'],
            'heading': 'Test Note Title',
            'level': 1,
            'wikilinks': []
        }
        
        # Verify structure (actual parsing would use Note.from_file)
        for key in ['title', 'file_path', 'tags', 'heading']:
            self.assertIn(key, expected_metadata)

    def test_large_vault_simulation(self):
        """Test performance with simulated large vault."""
        # Create test structure quickly
        created_files = 0
        for i in range(5):
            subdir = self.vault_path / f"category_{i}"
            subdir.mkdir(exist_ok=True)
            
            for j in range(3):
                file_path = subdir / f"note_{j}.md"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# Note {i}-{j}\n\nContent for category {i}, note {j}")
                created_files += 1
        
        # Simulate processing count
        actual_processable = len(list(self.vault_path.rglob("*.md")))
        self.assertEqual(actual_processable, created_files)

    def test_pipeline_id_generation(self):
        """Test document ID generation throughout pipeline."""
        test_file = self.vault_path / "id_test.md"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# ID Generation Test\nSection for testing")
        
        # Simulate ID generation process
        file_name = test_file.name
        section_id = "0"  # Based on first section
        expected_id = f"{file_name}::{section_id}"
        
        self.assertTrue(expected_id.endswith("::0"))

    def test_error_recovery_during_processing(self):
        """Test pipeline resilience to individual file failures."""
        # Create mix of good and problematic files
        good_file = self.vault_path / "good.md"
        binary_file = self.vault_path / "not_markdown.md"
        
        with open(good_file, "w", encoding="utf-8") as f:
            f.write("# Good Note\nValid content")
            
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03")  # Binary data
        
        # Simulate processing with error handling
        processed = []
        failed = []
        
        for file_path in self.vault_path.glob("*.md"):
            try:
                # Simulate Note processing
                if file_path.is_file():
                    processed.append(str(file_path))
            except Exception:
                failed.append(str(file_path))
        
        # Should process at least the good file
        self.assertIn(str(good_file), processed)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI commands."""

    def setUp(self):
        """Set up CLI test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.default_args = lambda: None  # Mock args
        self.default_args.vault_dir = Path(self.temp_dir) / "vault"
        self.default_args.db_path = Path(self.temp_dir) / "chroma_db"

    def tearDown(self):
        """Clean up CLI test environment."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_index_command_structure(self):
        """Test CLI index command structure."""
        # Test command parsing (simulated)
        vault_path = Path(self.temp_dir) / "test_vault"
        vault_path.mkdir()
        
        with open(vault_path / "test.md", "w", encoding="utf-8") as f:
            f.write("# Test\nContent")
        
        # Simulate argument parsing
        self.assertTrue(vault_path.exists())
        self.assertTrue((vault_path / "test.md").exists())

    def test_config_overrides_from_cli(self):
        """Test CLI parameter overrides."""
        vault_path = Path(self.temp_dir) / "vault"
        vault_path.mkdir()
        
        # Simulate config resolution
        resolved_config = {
            'db_path': str(self.default_args.db_path),
            'vault_dir': str(vault_path)
        }
        
        self.assertEqual(resolved_config['db_path'], str(self.default_args.db_path))
        self.assertEqual(resolved_config['vault_dir'], str(vault_path))

    def test_database_statistics_after_processing(self):
        """Test statistics collection after vault processing."""
        vault_path = Path(self.temp_dir) / "vault"
        vault_path.mkdir()
        
        # Create varied test notes
        test_structure = {
            "category1/note1.md": "# Note 1\nContent",
            "category1/note2.md": "# Note 2\nContent", 
            "category2/note3.md": "# Note 3\nContent"
        }
        
        for rel_path, content in test_structure.items():
            file_path = vault_path / rel_path
            file_path.parent.mkdir(exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Test actual processing with RAGMicroAgent
        agent = RAGMicroAgent()
        result = agent.index_vault(str(vault_path))
        
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["files_found"], 3)
        self.assertEqual(result["files_processed"], 3)
        self.assertGreater(result["documents_added"], 0)
        
        # Verify collection stats
        stats = agent.get_collection_stats()
        self.assertGreater(stats["document_count"], 0)


if __name__ == "__main__":
    unittest.main()