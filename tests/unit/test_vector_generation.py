"""
Tests for vector generation and payload format using real sample notes.
"""

import pytest
from datetime import datetime
from src.core.note import Note
from src.core.ingestion.processor import NoteProcessor


class TestVectorGeneration:
    """Test vector generation and payload formatting."""
    
    def test_point_payload_structure(self, real_sample_notes, vector_store_manager):
        """Test that Note objects convert to correct Qdrant payload structure."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")
            
        note = real_sample_notes[0]
        processor = NoteProcessor()
        
        # Process note and get documents with payload
        documents = list(processor.process_note(note))
        
        assert len(documents) > 0
        
        for doc in documents:
            metadata = doc.metadata
            
            # Verify required fields exist
            assert "title" in metadata
            assert "file_path" in metadata
            assert "created_date" in metadata
            assert "modified_date" in metadata
            assert "wikilinks" in metadata
            assert "heading" in metadata
            assert "level" in metadata
            assert "section_id" in metadata
            
            # Verify data types
            assert isinstance(metadata["title"], str)
            assert isinstance(metadata["file_path"], str)
            assert isinstance(metadata["created_date"], int)
            assert isinstance(metadata["modified_date"], int)
            assert isinstance(metadata["wikilinks"], list)
            assert isinstance(metadata["heading"], str)
            assert isinstance(metadata["level"], int)
            assert isinstance(metadata["section_id"], str)
            
            # Verify Unix timestamps are positive
            assert metadata["created_date"] > 0
            assert metadata["modified_date"] > 0
    
    def test_wikilink_content_extraction(self, real_sample_notes):
        """Test that wikilinks are extracted as plain text without brackets."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")
            
        # Find a note with wikilinks
        note_with_wikilinks = None
        for note in real_sample_notes:
            if note.wikilinks:
                note_with_wikilinks = note
                break
        
        if not note_with_wikilinks:
            pytest.skip("No notes with wikilinks found")
            
        # Verify wikilinks are plain text without brackets
        for wikilink in note_with_wikilinks.wikilinks:
            assert not wikilink.startswith("[[")
            assert not wikilink.endswith("]]")
            assert "[[" not in wikilink
            assert "]]" not in wikilink
            assert len(wikilink.strip()) > 0
    
    def test_multiple_wikilinks_extraction(self, real_sample_notes):
        """Test extraction of multiple wikilinks from a single note."""
        if not real_sample_notes:
            pytest.skip("No sample notes available")
            
        # Find note with multiple wikilinks
        multi_wikilink_note = None
        for note in real_sample_notes:
            if len(note.wikilinks) > 1:
                multi_wikilink_note = note
                break
        
        if not multi_wikilink_note:
            pytest.skip("No notes with multiple wikilinks found")
            
        # Verify all wikilinks are properly formatted
        assert len(multi_wikilink_note.wikilinks) >= 2
        for wikilink in multi_wikilink_note.wikilinks:
            assert isinstance(wikilink, str)
            assert wikilink.strip() == wikilink  # No leading/trailing spaces