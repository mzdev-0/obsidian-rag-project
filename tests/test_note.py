import unittest
import os
import glob
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from note import Note


class TestNoteInstantiation(unittest.TestCase):
    def test_create_note_from_file(self):
        test_notes_path = "obsidian-rag-project/test_notes/*.md"
        test_note_files = glob.glob(test_notes_path)

        for note_file in test_note_files:
            with self.subTest(note_file=note_file):
                note = Note.from_file(note_file)
                self.assertIsNotNone(note)
                print(f"--- Testing Note: {note.title} ---")
                print(f"File Path: {note.file_path}")
                print(f"Created Date: {note.created_date}")
                print(f"Modified Date: {note.modified_date}")
                print(f"Tags: {note.tag_wikilinks}")
                print(f"Wikilinks: {note.wikilinks}")
                print(f"URLs: {note.urls}")
                print("--- Content Sections ---")
                for section in note.content_sections:
                    print(f"  ID: {section.id}")
                    print(f"  Heading: {section.heading}")
                    print(f"  Level: {section.level}")
                    print(f"  Content: {section.content[:100]}...")
                print("-" * (len(note.title) + 20))


if __name__ == "__main__":
    unittest.main()
