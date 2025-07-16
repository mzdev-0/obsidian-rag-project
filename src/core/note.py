import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from . import parsing

logger = logging.getLogger(__name__)

Vector = list[float]


# @dataclass
# class Image:
#    """Represents an image within a note."""
#
#    path: str
#    ocr_text: Optional[str] = None
#    context: Optional[str] = None
#    embedding: Optional[Vector] = None


@dataclass
class Note:
    """A comprehensive representation of a single markdown note."""

    file_path: str
    _raw_content: str = field(repr=False)

    # --- Core Metadata ---
    title: str = field(init=False)
    created_date: datetime = field(init=False)
    modified_date: datetime = field(init=False)

    # --- Relational & Categorical Metadata ---
    references: list[str] = field(default_factory=list)
    wikilinks: list[str] = field(default_factory=list)
    tag_wikilinks: list[str] = field(default_factory=list)
    urls: list[str] = field(
        default_factory=list
    )  # urls found in the note content (May not want to collect separately)

    # --- Structured Content ---
    note_body: str = field(init=False)
    content_sections: list[parsing.ContentSection] = field(default_factory=list)
    #    images: List[Image] = field(default_factory=list)

    def __post_init__(self):
        """Initializes metadata and parses content."""
        self._extract_file_metadata()
        self._parse_content()

    def _extract_file_metadata(self):
        """Extracts metadata (title, dates) from the file system."""
        self.title = os.path.splitext(os.path.basename(self.file_path))[0]
        stat = os.stat(self.file_path)
        self.created_date = parsing.parse_datetime(
            self._raw_content
        ) or datetime.fromtimestamp(stat.st_mtime)
        self.modified_date = datetime.fromtimestamp(stat.st_mtime)

    def _parse_content(self):
        self.tag_wikilinks = parsing.parse_tags(self._raw_content)
        self.note_body = parsing.parse_body(self._raw_content)
        self.wikilinks = parsing.extract_wikilinks(self.note_body)
        self.content_sections = parsing.parse_headings(self.note_body)
        
        logger.debug(f"Parsed note {self.file_path}: {len(self.tag_wikilinks)} tags, {len(self.wikilinks)} wikilinks, {len(self.content_sections)} sections")
        
        if not self.note_body.strip():
            logger.warning(f"Note body empty after parsing: {self.file_path}")
            
        for i, section in enumerate(self.content_sections):
            logger.debug(f"Section {i+1}: '{section.heading}' ({len(section.content)} chars)")
            
        # self.images = parsing.extract_images(self._raw_content)

    @classmethod
    def from_file(cls, file_path: str) -> "Note":
        """Creates a Note instance from a file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Note file not found at: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            logger.info(f"Loaded note: {file_path} ({len(raw_content)} chars)")
            return cls(file_path=file_path, _raw_content=raw_content)
        except Exception as e:
            logger.error(f"Failed to load note from {file_path}: {e}")
            raise
