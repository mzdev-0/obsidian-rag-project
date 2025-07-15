
import unittest
from unittest.mock import patch
import os
import sys
import glob
import chromadb
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_rag_query
from src.core.note import Note
from src.core.embed import llama_embedder, create_embedding_text

class TestAgentEndToEnd(unittest.TestCase):
    """
    End-to-end integration tests for the RAG agent.
    
    This class sets up a temporary, real ChromaDB collection and uses
    a live LLM to validate the full `run_rag_query` workflow.
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up a temporary ChromaDB database and populate it with test notes.
        This is the same setup as in test_retriever.py to ensure consistency.
        """
        cls.db_path = "./test_chroma_db_agent"
        cls.collection_name = "test_agent_collection"
        
        # Point the agent to use this test DB path instead of the default
        # We do this by patching the chromadb.PersistentClient call in main.py
        cls.client_patcher = patch('main.chromadb.PersistentClient')
        cls.mock_client = cls.client_patcher.start()
        
        # Clean up any previous test runs
        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)
            
        # 1. Initialize ChromaDB client and collection
        cls.chroma_client = chromadb.PersistentClient(path=cls.db_path)
        cls.collection = cls.chroma_client.create_collection(name=cls.collection_name)
        
        # Configure the mock to return our test client and collection
        cls.mock_client.return_value = cls.chroma_client
        
        # 2. Process and embed notes
        note_files = glob.glob("data/sample_notes/*.md")
        all_documents = [create_embedding_text(n.title, s.heading, s.content) for n in [Note.from_file(f) for f in note_files] for s in n.content_sections]
        all_metadatas = [
            {
                "title": n.title, "file_path": n.file_path, "created_date": n.created_date.isoformat(),
                "modified_date": n.modified_date.isoformat(), "tags": ", ".join(n.tag_wikilinks),
                "wikilinks": ", ".join(n.wikilinks), "heading": s.heading, "level": s.level
            }
            for n in [Note.from_file(f) for f in note_files] for s in n.content_sections
        ]
        all_ids = [f"{n.file_path}::{s.heading}" for n in [Note.from_file(f) for f in note_files] for s in n.content_sections]

        if all_documents:
            cls.collection.add(
                documents=all_documents,
                metadatas=all_metadatas,
                ids=all_ids,
                embeddings=llama_embedder.embed_documents(all_documents)
            )

    @classmethod
    def tearDownClass(cls):
        """
        Clean up the temporary ChromaDB database and stop the patcher.
        """
        cls.client_patcher.stop()
        if os.path.exists(cls.db_path):
            shutil.rmtree(cls.db_path)

    def test_run_rag_query_specific_question(self):
        """
        Test a specific question that should trigger 'selective_context'.
        """
        # Arrange
        user_query = "What are the notable techniques used by APT 38?"
        
        # Act
        final_package = run_rag_query(user_query, collection=self.collection)
        
        # Assert
        self.assertNotIn("error", final_package)
        self.assertIn("results", final_package)
        self.assertGreater(len(final_package["results"]), 0)
        
        first_result = final_package["results"][0]
        self.assertIn("content", first_result)
        self.assertEqual(first_result["title"], "APT 38 - Financially Motivated APT TTPs")
        self.assertIn("UAC", first_result["content"]) # Check for specific content

    def test_run_rag_query_broad_question(self):
        """
        Test a broad question that should trigger 'metadata_only'.
        """
        # Arrange
        user_query = "Find my notes about file transfers"
        
        # Act
        final_package = run_rag_query(user_query, collection=self.collection)
        
        # Assert
        self.assertNotIn("error", final_package)
        self.assertIn("results", final_package)
        self.assertGreater(len(final_package["results"]), 0)
        
        first_result = final_package["results"][0]
        self.assertNotIn("content", first_result) # Key assertion for metadata_only
        self.assertIn("title", first_result)
        self.assertTrue(
            "File Transfer" in first_result["title"] or 
            "File Transfer" in first_result.get("tags", [])
        )

if __name__ == '__main__':
    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)
    unittest.main()
