"""
Test configuration for Qdrant unit tests.
Uses existing Qdrant server and real sample notes from ./data/sample_notes/
"""

import os
import pytest
from qdrant_client import QdrantClient
from pathlib import Path

from src.core.note import Note
from src.core.ingestion.vector_manager import VectorStoreManager
from src.core.ingestion.processor import NoteProcessor
from config import LLMConfig


@pytest.fixture
def test_collection_name():
    """Test collection name for unit tests."""
    return "test_obsidian_notes"


@pytest.fixture
def vector_store_manager(test_collection_name):
    """VectorStoreManager instance for test collection."""
    config = LLMConfig.from_env()
    config.qdrant_collection_name = test_collection_name
    return VectorStoreManager(config)


@pytest.fixture
def sample_notes_dir():
    """Path to real sample notes directory."""
    return Path("./data/sample_notes")


@pytest.fixture
def real_sample_notes(sample_notes_dir):
    """Load real sample notes from directory."""
    notes = []
    if sample_notes_dir.exists():
        for md_file in sample_notes_dir.glob("*.md"):
            try:
                note = Note.from_file(str(md_file))
                notes.append(note)
            except Exception as e:
                print(f"Warning: Could not load {md_file}: {e}")
    return notes


@pytest.fixture
def test_collection(vector_store_manager, test_collection_name):
    """Ensure test collection exists and is clean."""
    # Clean up existing test collection if it exists
    try:
        vector_store_manager.client.delete_collection(test_collection_name)
    except Exception:
        pass

    # Create fresh test collection
    vector_store_manager.clear_collection()
    return test_collection_name


@pytest.fixture
def indexed_notes(vector_store_manager, real_sample_notes, test_collection):
    """Index real sample notes into test collection."""
    if not real_sample_notes:
        return []

    processor = NoteProcessor(vector_store_manager=vector_store_manager)

    # Index notes in batches
    for note in real_sample_notes:
        processor.process_note(note)

    return real_sample_notes

