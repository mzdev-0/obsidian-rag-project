"""
Vector Store Manager for ChromaDB operations.

Handles document storage in ChromaDB using the existing LangChain integration,
providing a bridge between processed documents and the vector store.
"""

from typing import List, Optional, Tuple
import logging
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from config import get_embedding_function


def get_embedder():
    """Get embedding function with proper error handling."""
    try:
        return get_embedding_function()
    except RuntimeError as e:
        logger.warning(f"Using fallback embedding (error: {e})")
        return None


logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector store operations for note embeddings."""

    def __init__(self, db_path: str, collection_name: str = "obsidian_notes"):
        self.db_path = str(Path(db_path))
        self.collection_name = collection_name
        self.vectorstore = None
        self._initialize_vectorstore()

    def _initialize_vectorstore(self):
        """Initialize the Chroma vectorstore with the configured embedding function."""
        embedder = get_embedder()
        if embedder is None:
            raise RuntimeError("Embedding function not available")

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embedder,
            persist_directory=self.db_path,
        )

        logger.info(
            f"Initialized vector store at {self.db_path} with collection {self.collection_name}"
        )

    def store_document(self, content: str, metadata: dict, doc_id: str) -> None:
        """
        Store a single document with metadata.

        Args:
            content: The text content to store
            metadata: Dictionary with document metadata
            doc_id: Unique identifier for the document
        """
        try:
            doc = Document(page_content=content, metadata=metadata)

            self.vectorstore.add_documents([doc], ids=[doc_id])
            logger.debug(f"Stored document {doc_id}")

        except Exception as e:
            logger.error(f"Failed to store document {doc_id}: {e}")
            raise

    def store_documents(self, documents: List[Document], doc_ids: List[str]) -> None:
        """
        Store multiple documents at once.

        Args:
            documents: List of Document objects
            doc_ids: List of document IDs
        """
        if not documents:
            return

        try:
            self.vectorstore.add_documents(documents, ids=doc_ids)
            logger.info(f"Stored {len(documents)} documents")

        except Exception as e:
            logger.error(f"Failed to store documents: {e}")
            raise

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Get all document IDs
            all_docs = self.vectorstore._collection.get(include=["documents"])
            if all_docs and all_docs.get("ids"):
                self.vectorstore._collection.delete(ids=all_docs["ids"])
                logger.info("Cleared all documents from collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """Get metadata about the vector store collection."""
        try:
            count = self.vectorstore._collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "db_path": self.db_path,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "db_path": self.db_path,
                "error": str(e),
            }

    def document_exists(self, doc_id: str) -> bool:
        """Check if a document with given ID exists."""
        try:
            result = self.vectorstore._collection.get(
                ids=[doc_id], include=["metadatas"]
            )
            return bool(result.get("ids"))
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """Remove a specific document by ID."""
        try:
            self.vectorstore._collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Failed to remove document {doc_id}: {e}")
            return False

    def remove_documents_by_path(self, file_path: str) -> int:
        """
        Remove all documents associated with a specific file.

        Args:
            file_path: Path of the original file

        Returns:
            Number of documents removed
        """
        try:
            # Find documents matching the file path
            results = self.vectorstore._collection.get(
                where={"file_path": file_path}, include=["metadatas"]
            )

            if results and results.get("ids"):
                doc_ids = results["ids"]
                self.vectorstore._collection.delete(ids=doc_ids)
                return len(doc_ids)

            return 0
        except Exception as e:
            logger.error(f"Failed to remove documents by path {file_path}: {e}")
            return 0

    def search_documents(self, query: str, k: int = 5, filter_dict: Optional[dict] = None) -> List[Document]:
        """
        Search documents by semantic similarity.

        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of matching Document objects
        """
        try:
            return self.vectorstore.similarity_search(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_documents_with_scores(self, query: str, k: int = 5, filter_dict: Optional[dict] = None) -> List[Tuple[Document, float]]:
        """
        Search documents by semantic similarity with relevance scores.

        Args:
            query: Search query text
            k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            List of (Document, score) tuples
        """
        try:
            return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Search with scores failed: {e}")
            return []

    def get_documents_by_metadata(self, filter_dict: dict, limit: int = 100) -> List[Document]:
        """
        Get documents by metadata filtering (no semantic search).

        Args:
            filter_dict: ChromaDB-compatible filter
            limit: Maximum number of documents to return

        Returns:
            List of matching Document objects
        """
        try:
            results = self.vectorstore._collection.get(
                where=filter_dict,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            documents = []
            for i, doc_id in enumerate(results.get("ids", [])):
                if i < len(results.get("documents", [])) and i < len(results.get("metadatas", [])):
                    doc = Document(
                        page_content=results["documents"][i],
                        metadata=results["metadatas"][i]
                    )
                    documents.append(doc)
            
            return documents
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return []

    def get_collection_count(self) -> int:
        """Get the total number of documents in the collection."""
        try:
            return self.vectorstore._collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0

