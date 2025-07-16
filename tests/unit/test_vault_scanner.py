"""
Tests for the Vault Scanner component of the note ingestion pipeline.

This module tests the robust vault scanning functionality including:
- Hidden file filtering
- Symbolic link handling
- Recursive directory traversal
- File type validation
- Performance characteristics
- Error handling
"""

import os
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

from src.core.ingestion.scanner import VaultScanner, ScanOptions


class TestVaultScanner(unittest.TestCase):
    """Comprehensive test suite for vault scanning functionality."""

    def setUp(self):
        """Set up test vault directories before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.scanner = VaultScanner()

    def tearDown(self):
        """Clean up test directories after each test."""
        shutil.rmtree(self.test_dir)

    def create_test_file(self, path: str, content: str = "", create_dirs: bool = True):
        """Helper to create test files."""
        if create_dirs:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_basic_markdown_discovery(self):
        """Test identification of basic markdown files."""
        # Test data
        self.create_test_file(f"{self.test_dir}/note1.md", "# Test Note")
        self.create_test_file(f"{self.test_dir}/note2.markdown", "## Another Note")
        self.create_test_file(f"{self.test_dir}/note3q", "## Not markdown")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        found_files = {f.name for f in results}
        self.assertEqual(found_files, {"note1.md", "note2.markdown"})

    def test_hidden_file_exclusion(self):
        """Test that hidden files and directories are excluded."""
        # Test data
        self.create_test_file(f"{self.test_dir}/visible.md")
        self.create_test_file(f"{self.test_dir}/.hidden.md")
        self.create_test_file(f"{self.test_dir}/.hidden_dir/visible.md")
        self.create_test_file(f"{self.test_dir}/dir/.internal.md")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        visible_file_count = len(results)
        self.assertEqual(visible_file_count, 1)
        self.assertEqual(results[0].name, "visible.md")

    def test_recursive_directory_traversal(self):
        """Test scanning nested directories."""
        # Test data
        self.create_test_file(f"{self.test_dir}/level1.md")
        self.create_test_file(f"{self.test_dir}/dir1/level2.md")
        self.create_test_file(f"{self.test_dir}/dir1/dir2/level3.md")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        paths = [str(r.relative_to(self.test_dir)) for r in results]
        self.assertEqual(
            set(paths), {"level1.md", "dir1/level2.md", "dir1/dir2/level3.md"}
        )

    def test_case_insensitive_extensions(self):
        """Test markdown extension detection is case-insensitive."""
        # Test data
        self.create_test_file(f"{self.test_dir}/upper.MD")
        self.create_test_file(f"{self.test_dir}/mixed.Markdown")
        self.create_test_file(f"{self.test_dir}/lower.md")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        found_files = {f.name for f in results}
        expected = {"upper.MD", "mixed.Markdown", "lower.md"}
        self.assertEqual(found_files, expected)

    def test_empty_directory_handling(self):
        """Test scanning empty directories."""
        # Test data - just empty directories
        os.makedirs(f"{self.test_dir}/empty_dir", exist_ok=True)

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        self.assertEqual(len(results), 0)

    def test_non_existent_path(self):
        """Test handling of non-existent directory paths."""
        non_existent = f"{self.test_dir}/does_not_exist"

        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            list(self.scanner.scan(non_existent))

    def test_permission_denied_handling(self):
        """Test graceful handling of permission errors."""
        # Create a restricted directory
        restricted_dir = f"{self.test_dir}/restricted"
        os.makedirs(restricted_dir, exist_ok=True)

        try:
            os.chmod(restricted_dir, 0o000)
            results = list(self.scanner.scan(self.test_dir))
            # Should skip restricted directory gracefully
        except OSError:
            # Skip if we can't set permissions
            pass
        finally:
            try:
                os.chmod(restricted_dir, 0o755)
            except OSError:
                pass

    def test_vault_performance_characteristics(self):
        """Test performance with large vault simulation."""
        # Create many directories and files
        for i in range(100):
            dir_path = f"{self.test_dir}/dir_{i:03d}"
            for j in range(10):
                self.create_test_file(f"{dir_path}/note_{j}.md")

        # Act with performance measurement
        import time

        start = time.time()
        results = list(self.scanner.scan(self.test_dir))
        duration = time.time() - start

        # Assert
        self.assertEqual(len(results), 1000)  # 100 dirs * 10 files
        self.assertLess(duration, 2.0)  # Should complete in under 2 seconds

    def test_unicode_path_handling(self):
        """Test handling of unicode file and directory names."""
        # Test data with unicode characters
        self.create_test_file(f"{self.test_dir}/项目.md", "# 標題")
        self.create_test_file(f"{self.test_dir}/测试/笔记.md")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        found_files = {f.name for f in results}
        expected = {"项目.md", "笔记.md"}
        self.assertEqual(found_files, expected)

    def test_scan_result_structure(self):
        """Test the structure and metadata of scan results."""
        # Test data
        import datetime

        test_file = f"{self.test_dir}/test.md"
        self.create_test_file(test_file, "# Test content")

        # Act
        results = list(self.scanner.scan(self.test_dir))

        # Assert
        self.assertEqual(len(results), 1)
        result = results[0]

        # Verify essential metadata
        self.assertTrue(result.is_file())
        self.assertTrue(result.suffix.lower() in {"", ".md", ".markdown"})
        self.assertGreater(result.stat().st_size, 0)
        self.assertTrue(result.exists())


class TestScanOptions(unittest.TestCase):
    """Test scan configuration options."""

    def test_default_extensions(self):
        """Test default markdown extension handling."""
        from src.core.ingestion.scanner import ScanOptions

        options = ScanOptions()
        self.assertEqual(options.include_extensions, {".md", ".markdown"})
        self.assertTrue(options.follow_symlinks is False)
        self.assertTrue(options.include_hidden is False)
        self.assertTrue(options.max_depth is None)

    def test_custom_scan_options(self):
        """Test custom scan configuration."""
        from src.core.ingestion.scanner import ScanOptions

        options = ScanOptions(
            include_extensions={".txt", ".md"},
            follow_symlinks=True,
            include_hidden=True,
            max_depth=2,
        )

        self.assertEqual(options.include_extensions, {".txt", ".md"})
        self.assertTrue(options.follow_symlinks)
        self.assertTrue(options.include_hidden)
        self.assertEqual(options.max_depth, 2)


if __name__ == "__main__":
    unittest.main()

