"""
Note Processing Engine for Embedding Generation Pipeline.

This module handles the conversion from Note objects (already implemented)
to document-sections suitable for embedding generation and ChromaDB storage.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Iterator, Optional
from dataclasses import dataclass
from datetime import datetime

# Import existing components
from ..note import Note
from ..parsing import ContentSection

logger = logging.getLogger(__name__)


@dataclass
class ProcessedDocument:
    """A document ready for embedding and vector store storage."""

    id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None


class NoteProcessor:
    """Converts Note objects into ProcessedDocuments for embedding pipeline."""

    def process_note(self, note: Note) -> Iterator[ProcessedDocument]:
        """
        Convert a Note into ProcessedDocuments using pre-parsed content sections.

        Uses the Note object's existing content_sections (already parsed during Note creation)
        to avoid redundant parsing work.

        Args:
            note: The Note object to process

        Yields:
            ProcessedDocument objects ready for embedding
        """
        if not note.content_sections:
            logger.warning(f"Note {note.file_path} has no parseable content")
            return
            
        for section in note.content_sections:
            if section.content.strip():
                yield self._create_document_from_section(note, section)

    def process_file(self, file_path: str) -> Iterator[ProcessedDocument]:
        """
        Process a single markdown file through the pipeline.

        Args:
            file_path: Path to the markdown file

        Yields:
            ProcessedDocument objects
        """
        try:
            note = Note.from_file(file_path)
            documents = list(self.process_note(note))
            logger.info(f"Processed file {file_path} into {len(documents)} documents")
            yield from documents
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            raise ValueError(f"Failed to process {file_path}: {e}")

    ##def _create_document_from_note_body(self, note: Note) -> ProcessedDocument:
    ##    """Create a document from the entire note body."""
    ##    file_path = note.file_path
    ##    file_name = Path(file_path).stem
    ##
    ##    # Create embedding text following proper format
    ##    content = self.create_embedding_text(note.title, file_name, note.note_body.strip())
    ##
    ##    return ProcessedDocument(
    ##        id=self._generate_document_id(file_path, "full"),
    ##        content=content,
    ##        metadata=self._create_metadata(note, "", 0)
    ##    )

    def create_embedding_text(self, title: str, heading: str, content: str) -> str:
        """Format text for embedding generation in the new pipeline."""
        return f"{title} | {heading}\n\n{content}".strip()

    def _create_document_from_section(
        self, note: Note, section: ContentSection
    ) -> ProcessedDocument:
        """Create a document from a specific content section."""
        file_path = note.file_path

        # Create embedding text following proper format
        content = self.create_embedding_text(
            note.title, section.heading, section.content
        )
        
        logger.debug(f"Processing section '{section.heading}' from {file_path} ({len(section.content)} chars)")

        return ProcessedDocument(
            id=self._generate_document_id(file_path, section.id),
            content=content,
            metadata=self._create_metadata(note, section.heading, section.level),
        )

    def _create_document_from_note_body(self, note: Note) -> ProcessedDocument:
        """Create a document from the entire note body."""
        file_path = note.file_path
        file_name = Path(file_path).stem

        # Create embedding text following proper format
        content = self.create_embedding_text(
            note.title, file_name, note.note_body.strip()
        )

        return ProcessedDocument(
            id=self._generate_document_id(file_path, "full"),
            content=content,
            metadata=self._create_metadata(note, "", 0),
        )

    def _generate_document_id(self, file_path: str, section_id: str) -> str:
        """Generate unique document ID based on file path and section."""
        # Use relative path from vault root for portability
        path = Path(file_path)
        relative_path = path.name

        # Replace path separators and create safe ID
        safe_name = str(relative_path).replace("/", "_").replace(" ", "_")
        return f"{safe_name}::{section_id}"

    def _create_metadata(self, note: Note, heading: str, level: int) -> Dict:
        """Create metadata dictionary for ChromaDB storage."""
        # Convert lists to comma-separated strings for ChromaDB compatibility
        tags_str = ",".join(note.tag_wikilinks) if note.tag_wikilinks else ""
        wikilinks_str = ",".join(note.wikilinks) if note.wikilinks else ""
        
        return {
            "title": note.title,
            "file_path": str(note.file_path),
            "heading": heading,
            "level": level,
            "tags": tags_str,
            "wikilinks": wikilinks_str,
            "created_date": note.created_date.isoformat(),
            "modified_date": note.modified_date.isoformat(),
        }

