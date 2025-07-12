import glob
import os
import chromadb
from note import Note
from embed import llama_embedder, create_embedding_text


def main():
    print("Starting RAG PoC...")

    # 1. Instantiate ChromaDB client and collection
    try:
        chroma_client = chromadb.PersistentClient(path="./chromadb")
        collection = chroma_client.get_or_create_collection(name="obsidian_notes")
        print("✅ ChromaDB client and collection initialized.")
    except Exception as e:
        print(f"❌ Error initializing ChromaDB: {e}")
        return

    # 2. Find all notes in the test_notes directory
    note_files = glob.glob("test_notes/*.md")
    if not note_files:
        print("❌ No notes found in 'test_notes/' directory.")
        return

    print(f"Found {len(note_files)} notes to process.")

    all_documents = []
    all_metadatas = []
    all_ids = []

    # 3. Process each note
    for note_file in note_files:
        try:
            note = Note.from_file(note_file)
            print(f"  - Processing Note: {note.title}")

            # 4. Chunk by heading and prepare for embedding
            for section in note.content_sections:
                # Create a unique ID for each section
                section_id = f"{note.file_path}::{section.heading}"

                # Prepare the text for embedding
                embedding_text = create_embedding_text(
                    title=note.title, heading=section.heading, content=section.content
                )

                # Prepare the metadata
                metadata = {
                    "title": note.title,
                    "file_path": note.file_path,
                    "created_date": str(note.created_date),
                    "modified_date": str(note.modified_date),
                    "tags": ", ".join(note.tag_wikilinks),
                    "wikilinks": ", ".join(note.wikilinks),
                    "heading": section.heading,
                    "level": section.level,
                }

                all_documents.append(embedding_text)
                all_metadatas.append(metadata)
                all_ids.append(section_id)

        except Exception as e:
            print(f"❌ Error processing note {note_file}: {e}")

    # 5. Add all documents to ChromaDB in a single batch
    if all_documents:
        try:
            collection.add(
                documents=all_documents,
                metadatas=all_metadatas,
                ids=all_ids,
            )
            print(
                f"\n✅ Successfully added {len(all_documents)} documents to ChromaDB."
            )

            # Optional: Verify by querying the collection
            retrieved_items = collection.get(limit=5)
            print("\n--- Sample of items in ChromaDB ---")
            for i, item_id in enumerate(retrieved_items["ids"]):
                print(f"  ID: {item_id}")
                print(f"  Metadata: {retrieved_items['metadatas'][i]}")  # pyright: ignore
            print("-" * 35)

        except Exception as e:
            print(f"❌ Error adding documents to ChromaDB: {e}")

    print("\nPoC finished.")


if __name__ == "__main__":
    main()
