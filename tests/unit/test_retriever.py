import unittest
import os
import sys
import glob
import shutil

# This allows the test runner to find modules in the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# LangChain and project-specific imports
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from src.core.note import Note
from src.core.embed import llama_embedder, create_embedding_text
from src.core.retriever import retrieve_context


class TestRetrieverIntegration(unittest.TestCase):
    """
    Integration tests for the Retriever module, now using the correct,
    LangChain-idiomatic approach for database setup.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up persistent test database that won't be recreated unless source files change.
        Checksum test files to determine if rebuild needed.
        """
        cls.db_path = "../.test_chroma_db_persistent"
        cls.collection_name = "test_retriever_lc_collection"
        cls.note_files_path = "/home/cas/projects/obsidian-rag-project/test_notes/*.md"
        
        import hashlib
        
        # Generate checksum of test files to detect changes
        note_files = sorted(glob.glob(cls.note_files_path))
        if not note_files:
            raise FileNotFoundError(
                f"No test notes found at path: {cls.note_files_path}"
            )
            
        hasher = hashlib.md5()
        for file_path in note_files:
            with open(file_path, 'rb') as f:
                hasher.update(f.read())
        current_checksum = hasher.hexdigest()
        checksum_file = os.path.join(cls.db_path, ".test_checksum")
        
        # Check if we need to rebuild
        rebuild_needed = True
        if os.path.exists(checksum_file):
            with open(checksum_file, 'r') as f:
                if f.read().strip() == current_checksum:
                    rebuild_needed = False
        
        if rebuild_needed:
            # Clean old DB and create new one
            if os.path.exists(cls.db_path):
                shutil.rmtree(cls.db_path)
                
            # 1. Prepare LangChain Document objects
            langchain_docs = []
            cls.sections_per_note = {}
            for note_file in note_files:
                note = Note.from_file(note_file)
                cls.sections_per_note[note.title] = len(note.content_sections)
                for section in note.content_sections:
                    embedding_text = create_embedding_text(
                        note.title, section.heading, section.content
                    )
                    metadata = {
                        "title": note.title,
                        "file_path": note.file_path,
                        "created_date": note.created_date.isoformat(),
                        "modified_date": note.modified_date.isoformat(),
                        "tags": ",".join(note.tag_wikilinks) if note.tag_wikilinks else "",
                        "wikilinks": ",".join(note.wikilinks) if note.wikilinks else "",
                        "heading": section.heading,
                        "level": section.level,
                    }
                    doc = Document(page_content=embedding_text, metadata=metadata)
                    langchain_docs.append(doc)

            if not langchain_docs:
                raise ValueError("No documents were created to populate the test database.")

            cls.vectorstore = Chroma.from_documents(
                documents=langchain_docs,
                embedding=llama_embedder,
                collection_name=cls.collection_name,
                persist_directory=cls.db_path,
            )
            
            # Write checksum
            os.makedirs(cls.db_path, exist_ok=True)
            with open(checksum_file, 'w') as f:
                f.write(current_checksum)
            
            print(f"Rebuilt test database at {cls.db_path}")
        else:
            # Load existing vectorstore
            cls.vectorstore = Chroma(
                collection_name=cls.collection_name,
                embedding_function=llama_embedder,
                persist_directory=cls.db_path,
            )
            
            # Recreate sections per note mapping for tests
            cls.sections_per_note = {}
            for note_file in note_files:
                note = Note.from_file(note_file)
                cls.sections_per_note[note.title] = len(note.content_sections)
            
            print(f"Using existing test database at {cls.db_path}")

    @classmethod
    def tearDownClass(cls):
        """Keep test database persistent across runs - don't delete it."""
        pass

    # --- Test cases remain unchanged as they were already correct ---

    def test_semantic_query_returns_relevant_context(self):
        """Test a conceptual query returns relevant, deduplicated results."""
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "How to avoid detection when transferring files?",
            "filters": [],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.vectorstore)
        self.assertIn("results", context_package)
        self.assertGreater(len(context_package["results"]), 0)
        # Allow for different relevant results due to embedding similarities
        found_titles = [result["title"] for result in context_package["results"][:3]]  # Check top 3
        relevant_found = any(title in ["Evading Detection when Transferring Files", "Transferring Files with Python"] 
                           for title in found_titles)
        self.assertTrue(relevant_found, 
                       f"Expected relevant file transfer content not found in top results: {found_titles[:5]}")

    def test_metadata_get_does_not_deduplicate_results(self):
        """CRITICAL: Test the 'get' path returns all matching sections from a single note."""
        note_title_to_test = "Filtering Redirector"
        expected_sections = self.sections_per_note.get(note_title_to_test, 0)
        self.assertGreater(
            expected_sections,
            1,
            f"Test setup error: Note '{note_title_to_test}' must have multiple sections.",
        )

        query_plan = {
            "semantic_search_needed": False,
            "semantic_query": "",
            "filters": [
                {"field": "title", "operator": "$eq", "value": note_title_to_test}
            ],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.vectorstore)
        self.assertIn("results", context_package)
        self.assertEqual(
            len(context_package["results"]),
            expected_sections,
            "A 'get' op should not deduplicate results.",
        )


if __name__ == "__main__":
    unittest.main()
