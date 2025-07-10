import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import parsing

Vector = List[float]


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
    tags: List[str] = field(default_factory=list)
    wikilinks: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    # --- Structured Content ---
    content_sections: List[parsing.ContentSection] = field(default_factory=list)
    #    images: List[Image] = field(default_factory=list)

    def __post_init__(self):
        """Initializes metadata and parses content."""
        self._extract_file_metadata()
        self._parse_content()

    def _extract_file_metadata(self):
        """Extracts metadata (title, dates) from the file system."""
        self.title = os.path.splitext(os.path.basename(self.file_path))[0]
        stat = os.stat(self.file_path)
        self.created_date = datetime.fromtimestamp(stat.st_ctime)
        self.modified_date = datetime.fromtimestamp(stat.st_mtime)

    def _parse_content(self):
        self.wikilinks = parsing.extract_wikilinks(self._raw_content)
        self.content_sections = parsing.parse_headings(self._raw_content)
        # self.images = parsing.extract_images(self._raw_content)

    @classmethod
    def from_file(cls, file_path: str) -> "Note":
        """Creates a Note instance from a file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Note file not found at: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        return cls(file_path=file_path, _raw_content=raw_content)
