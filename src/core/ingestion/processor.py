"""
Note Processing Engine - Clean Architecture

Directly converts Note objects to LangChain Documents using pre-parsed content sections.
Eliminates redundant parsing and intermediate data models.
"""

import logging
from pathlib import Path
from typing import Iterator
from langchain.schema import Document

from ..note import Note
from ..parsing import ContentSection

logger = logging.getLogger(__name__)


class NoteProcessor:
    """Converts Note objects directly to LangChain Documents for vector storage."""

    def process_note(self, note: Note) -> Iterator[Document]:
        """
        Convert a Note into LangChain Documents using pre-parsed content sections.

        Args:
            note: The Note object to process

        Yields:
            LangChain Document objects ready for vector storage
        """
        if not note.content_sections:
            logger.warning(f"Note {note.file_path} has no parseable content")
            return
            
        for section in note.content_sections:
            if section.content.strip():
                yield self._section_to_document(note, section)

    def process_file(self, file_path: str) -> Iterator[Document]:
        """
        Process a single markdown file through the pipeline.

        Args:
            file_path: Path to the markdown file

        Yields:
            LangChain Document objects
        """
        try:
            note = Note.from_file(file_path)
            documents = list(self.process_note(note))
            logger.info(f"Processed file {file_path} into {len(documents)} documents")
            yield from documents
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            raise ValueError(f"Failed to process {file_path}: {e}")

    def _section_to_document(self, note: Note, section: ContentSection) -> Document:
        """Convert a ContentSection to a LangChain Document."""
        content = f"{note.title} | {section.heading}\n\n{section.content}".strip()
        
        metadata = {
            "title": note.title,
            "file_path": str(note.file_path),
            "heading": section.heading,
            "level": section.level,
            "tags": ",".join(note.tag_wikilinks) if note.tag_wikilinks else "",
            "wikilinks": ",".join(note.wikilinks) if note.wikilinks else "",
            "created_date": note.created_date.isoformat(),
            "modified_date": note.modified_date.isoformat(),
        }
        
        doc_id = f"{Path(note.file_path).stem}::{section.id}"
        return Document(page_content=content, metadata=metadata)