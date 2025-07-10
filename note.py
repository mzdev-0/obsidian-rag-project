
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

# Using a generic type for vector embeddings for flexibility.
Vector = List[float]

@dataclass
class Image:
    """
    Represents an image found within a note, aligned with the RAG system PRD.
    This structure separates visual content from text for distinct embedding strategies.
    """
    path: str
    ocr_text: Optional[str] = None
    context: Optional[str] = None  # Surrounding text to give context to the image.
    embedding: Optional[Vector] = None

@dataclass
class ContentSection:
    """
    Represents a structured chunk of text content from a note, typically under a heading.
    This allows for granular, heading-based chunking as specified in the RAG PRD.
    """
    id: str
    heading: str
    content: str
    level: int  # (e.g., 1 for #, 2 for ##)
    embedding: Optional[Vector] = None

@dataclass
class Note:
    """
    A comprehensive representation of a single note, designed to serve both the 
    Pre-processor and the RAG system as defined in their respective PRDs.

    This class is responsible for holding all metadata, structured content, and
    relational links parsed from a markdown file.
    """
    file_path: str
    
    # --- Core Metadata ---
    title: str = field(init=False)
    created_date: datetime = field(init=False)
    modified_date: datetime = field(init=False)
    
    # --- Relational & Categorical Metadata ---
    tags: List[str] = field(default_factory=list)
    wikilinks: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    
    # --- Structured Content ---
    content_sections: List[ContentSection] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    
    # --- Raw Content ---
    _raw_content: str = field(repr=False)

    def __post_init__(self):
        """Orchestrates the parsing of the note after initialization."""
        self._extract_file_metadata()
        self._parse_content()

    def _extract_file_metadata(self):
        """Extracts metadata from the file system."""
        self.title = os.path.splitext(os.path.basename(self.file_path))[0]
        stat = os.stat(self.file_path)
        self.created_date = datetime.fromtimestamp(stat.st_ctime)
        self.modified_date = datetime.fromtimestamp(stat.st_mtime)

    def _parse_content(self):
        """
        Parses the raw content of the note to populate structured fields.
        This method acts as a placeholder for the detailed parsing logic required
        by both PRDs, such as wikilink extraction, heading-based chunking, and
        metadata extraction from frontmatter.
        """
        # Placeholder for wikilink extraction (Pre-processor & RAG PRD)
        # e.g., self.wikilinks = re.findall(r"\[\[(.*?)\]\]", self._raw_content)
        pass
        
        # Placeholder for tag extraction (from frontmatter or inline)
        # e.g., parse YAML frontmatter
        pass

        # Placeholder for URL extraction (Pre-processor PRD)
        # e.g., self.urls = re.findall(r"http[s]?://...", self._raw_content)
        pass

        # Placeholder for heading-based chunking (RAG PRD)
        # This would involve splitting the content by markdown headings
        # and creating ContentSection objects.
        pass

        # Placeholder for image link extraction (RAG PRD)
        # e.g., find markdown image links ![[image.png]] or ![](path/to/image.png)
        pass

    @classmethod
    def from_file(cls, file_path: str) -> "Note":
        """Factory method to create a Note instance from a file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Note file not found at: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        return cls(file_path=file_path, _raw_content=raw_content)

# Example usage to demonstrate how the class would be instantiated and used.
if __name__ == '__main__':
    # Create a dummy file for demonstration purposes.
    dummy_dir = 'temp_notes'
    os.makedirs(dummy_dir, exist_ok=True)
    dummy_file_path = os.path.join(dummy_dir, 'example_note.md')
    
    dummy_content = """---
tags: [example, project, RAG]
---
# This is the Main Title

This is the first section of the note. It contains a link to another note [[Another Note]].

## Subsection 1.1
Here is some more detailed content and an external link: https://example.com.

This section also includes an image: ![[diagram.png]]
"""
    
    with open(dummy_file_path, 'w', encoding='utf-8') as f:
        f.write(dummy_content)

    try:
        # Instantiate the note using the factory method.
        note = Note.from_file(dummy_file_path)
        
        # The parsing logic in _parse_content is just a placeholder,
        # so we manually populate some fields to demonstrate the structure.
        note.tags = ['example', 'project', 'RAG']
        note.wikilinks = ['Another Note']
        note.urls = ['https://example.com']
        note.content_sections = [
            ContentSection(id='sec-1', heading='This is the Main Title', content='...', level=1),
            ContentSection(id='sec-2', heading='Subsection 1.1', content='...', level=2)
        ]
        note.images = [Image(path='diagram.png')]

        print("Successfully created and populated Note object:")
        print(f"  File Path: {note.file_path}")
        print(f"  Title: {note.title}")
        print(f"  Modified Date: {note.modified_date}")
        print(f"  Tags: {note.tags}")
        print(f"  Wikilinks: {note.wikilinks}")
        print(f"  Sections: {len(note.content_sections)}")
        print(f"  Images: {len(note.images)}")

    except FileNotFoundError as e:
        print(e)
    finally:
        # Clean up the dummy file and directory.
        import shutil
        if os.path.exists(dummy_dir):
            shutil.rmtree(dummy_dir)

