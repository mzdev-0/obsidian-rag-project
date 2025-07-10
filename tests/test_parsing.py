import unittest
import os
from dataclasses import dataclass, field
from typing import List, Optional
from parsing import parse_headings, extract_wikilinks

@dataclass
class ContentSection:
    """Represents a structured section of content from a note."""

    id: str
    heading: str
    content: str
    level: int  # e.g., 1 for #, 2 for ##
    embedding: Optional[List[float]] = None

class TestParsing(unittest.TestCase):

    def _read_test_note(self, filename):
        with open(os.path.join('obsidian-rag-project/test_notes', filename), 'r') as f:
            return f.read()

    def test_ignore_content_before_first_heading(self):
        content = self._read_test_note('2025 Threat Report - Huntress.md')
        sections = parse_headings(content)
        self.assertGreater(len(sections), 0)
        self.assertEqual(sections[0].heading, "Top Takeaways")
        self.assertNotIn("06-22-2025", sections[0].content)

    def test_multiple_heading_levels(self):
        content = self._read_test_note('APT 38 - Financially Motivated APT TTPs.md')
        sections = parse_headings(content)
        self.assertGreater(len(sections), 0)
        self.assertEqual(sections[0].heading, "Notable Techniques")
        self.assertEqual(sections[0].level, 3)

    def test_note_with_code_blocks(self):
        content = self._read_test_note('Downloading and Uploading Files in Powershell.md')
        sections = parse_headings(content)
        self.assertGreater(len(sections), 0)
        self.assertEqual(sections[0].heading, "Example")
        self.assertIn("New-Object Net.WebClient", sections[0].content)
        self.assertEqual(sections[1].heading, "Transfering Files from an FTP Server Using PowerShell")
        self.assertEqual(sections[2].heading, "PowerShell Script to Upload a File to Python Upload Server")

    def test_note_with_no_headings(self):
        content = "This note has no headings. It's just plain text."
        sections = parse_headings(content)
        self.assertEqual(len(sections), 0)

    def test_empty_note(self):
        content = ""
        sections = parse_headings(content)
        self.assertEqual(len(sections), 0)

    def test_note_with_only_headings(self):
        content = "# Heading 1\n## Heading 2\n### Heading 3"
        sections = parse_headings(content)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].heading, "Heading 1")
        self.assertEqual(sections[0].content, "")
        self.assertEqual(sections[1].heading, "Heading 2")
        self.assertEqual(sections[1].content, "")
        self.assertEqual(sections[2].heading, "Heading 3")
        self.assertEqual(sections[2].content, "")

class TestWikilinkExtraction(unittest.TestCase):

    def test_extract_wikilinks_simple(self):
        content = "This is a test with a [[simple link]]."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, ["simple link"])

    def test_extract_wikilinks_with_alias(self):
        content = "This is a test with an [[actual link|aliased link]]."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, ["actual link"])

    def test_extract_wikilinks_multiple(self):
        content = "Here are [[link one]] and [[link two]]."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, ["link one", "link two"])

    def test_extract_wikilinks_ignore_images(self):
        content = "This should be ignored: [[image.png]]. But this [[not an image]] should be captured."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, ["not an image"])

    def test_extract_wikilinks_no_links(self):
        content = "There are no wikilinks in this text."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, [])

    def test_extract_wikilinks_empty_string(self):
        content = ""
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, [])

    def test_extract_wikilinks_with_special_chars(self):
        content = "Link with special chars [[link-with-hyphens_and_underscores]]."
        wikilinks = extract_wikilinks(content)
        self.assertEqual(wikilinks, ["link-with-hyphens_and_underscores"])

if __name__ == '__main__':
    unittest.main()
