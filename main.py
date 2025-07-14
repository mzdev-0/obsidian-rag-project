import unittest
import os
import sys
import glob
import shutil

# This allows the test runner to find modules in the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# LangChain and project-specific imports
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from note import Note
from embed import llama_embedder, create_embedding_text
from retriever import retrieve_context


class TestRetrieverIntegration(unittest.TestCase):
    """
    Integration tests for the Retriever module, refactored to use the
    correct, modern LangChain-idiomatic approach for database population.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a temporary ChromaDB database using LangChain's Chroma wrapper,
        which handles the embedding process automatically via the `.from_documents()` method.
        """
        cls.db_path = "./test_chroma_db_lc"
        cls.collection_name = "test_retriever_lc_collection"
        cls.note_files_path = "obsidian-rag-project/test_notes/*.md"

        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)

        note_files = glob.glob(cls.note_files_path)
        if not note_files:
            raise FileNotFoundError(
                f"No test notes found at path: {cls.note_files_path}"
            )

        # 1. Prepare LangChain Document objects from your source files
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
                    "tags": note.tag_wikilinks,
                    "wikilinks": note.wikilinks,
                    "heading": section.heading,
                    "level": section.level,
                }

                # Create a LangChain Document for each section
                doc = Document(page_content=embedding_text, metadata=metadata)
                langchain_docs.append(doc)

        # 2. Use the CORRECT LangChain method to create and populate the collection in one step.
        # This is the key change. `from_documents` creates the embeddings and stores them.
        if langchain_docs:
            cls.vectorstore = Chroma.from_documents(
                documents=langchain_docs,
                embedding=llama_embedder,
                collection_name=cls.collection_name,
                persist_directory=cls.db_path,
            )

        # 3. For testing, we need the raw chromadb collection object that our retriever function expects.
        # We can get this directly from the LangChain vectorstore object.
        cls.collection = cls.vectorstore._collection

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary ChromaDB database after all tests."""
        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)

    # --- Test cases remain unchanged as they operate on the final collection ---

    def test_semantic_query_returns_relevant_context(self):
        """Test a conceptual query returns relevant, deduplicated results."""
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "How to evade detection?",
            "filters": [],
            "response_format": "selective_context",
        }
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)
        self.assertGreater(len(context_package["results"]), 0)
        self.assertEqual(
            context_package["results"][0]["title"],
            "Evading Detection when Transferring Files",
        )

    def test_metadata_get_does_not_deduplicate_results(self):
        """CRITICAL: Test the 'get' path returns all matching sections."""
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
        context_package = retrieve_context(query_plan, self.collection)
        self.assertIn("results", context_package)
        self.assertEqual(
            len(context_package["results"]),
            expected_sections,
            "A 'get' op should not deduplicate results.",
        )


if __name__ == "__main__":
    unittest.main()
