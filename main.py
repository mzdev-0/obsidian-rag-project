from note import Note
import parsing


def main():
    print("Hello from obsidian-rag-project!")

    note = Note.from_file("./test_notes/Evading Detection when Transferring Files.md")
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
    main()
