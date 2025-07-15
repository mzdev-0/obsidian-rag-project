"""
Pytest configuration and shared fixtures for RAG micro-agent tests.
"""

import sys
import os
import pytest
from unittest.mock import Mock
import tempfile
import shutil

# Add src to the Python path for all tests
def pytest_configure(config):
    """Configure pytest to add the src directory to PYTHONPATH."""
    src_path = os.path.join(os.path.dirname(__file__), '..')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


@pytest.fixture
def temp_db_dir():
    """Provide a temporary directory for ChromaDB testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def sample_note_content():
    """Provide sample markdown note content for testing."""
    return """# Main Heading

## Section 1
This is the first section content with some [[wikilink]] and [[#important-tag]] references.

## Section 2
This is the second section with **markdown** formatting and another reference [[Another Note]]."""


@pytest.fixture
def mock_vectorstore():
    """Provide a mock ChromaDB vectorstore for testing."""
    mock_store = Mock()
    mock_store._collection = Mock()
    mock_store.similarity_search = Mock(return_value=[])
    return mock_store