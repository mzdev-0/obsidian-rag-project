"""
Vector Store Manager for ChromaDB operations.

Handles document storage in ChromaDB using the existing LangChain integration,
providing a bridge between processed documents and the vector store.
"""

from typing import List, Optional, Tuple
import logging
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document

from config import LLMConfig, get_embedding_function


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

    def __init__(self, config: LLMConfig):
        self.config = config
        self.collection_name = config.qdrant_collection_name
        self.client = QdrantClient(
            url=config.qdrant_url, api_key=config.qdrant_api_key, timeout=60
        )
        self.vectorstore = None
        self._initialize_vectorstore()
        self._create_payload_indexes()

    def _initialize_vectorstore(self):
        """Initialize the Qdrant vectorstore with the configured embedding function."""
        embedder = get_embedder()
        if embedder is None:
            raise RuntimeError("Embedding function not available")

        # Create collection if it doesn't exist
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.config.qdrant_vector_size, distance=Distance.COSINE
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

        # Initialize LangChain integration
        self.vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=embedder,
            collection_name=self.collection_name,
            url=self.config.qdrant_url,
            api_key=self.config.qdrant_api_key,
        )

        logger.info(
            f"Initialized Qdrant vector store at {self.config.qdrant_url} with collection {self.collection_name}"
        )

    def _create_payload_indexes(self):
        """Create optimized payload indexes for all metadata fields."""
        indexes = [
            ("title", "keyword"),
            ("file_path", "keyword"),
            ("created_date", "datetime"),
            ("modified_date", "datetime"),
            ("tags", "keyword"),
            ("wikilinks", "keyword"),
            ("heading", "keyword"),
            ("level", "integer"),
            ("section_id", "keyword"),
        ]

        for field_name, index_type in indexes:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_type=index_type,
                )
                logger.debug(f"Created payload index for {field_name}")
            except Exception as e:
                logger.debug(f"Index for {field_name} may already exist: {e}")

    def store_document(self, content: str, metadata: dict) -> None:
        """
        Store a single document with metadata.

        Args:
            content: The text content to store
            metadata: Dictionary with document metadata
            doc_id: Unique identifier for the document
        """
        try:
            doc = Document(page_content=content, metadata=metadata)

            doc_id = metadata["id"]
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
            self.client.delete_collection(self.collection_name)
            self._initialize_vectorstore()
            logger.info("Cleared Qdrant collection")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def get_collection_stats(self) -> dict:
        """Get metadata about the vector store collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_documents": info.points_count,
                "collection_name": self.collection_name,
                "qdrant_url": self.config.qdrant_url,
                "vector_size": self.config.qdrant_vector_size,
                "indexed_fields": [
                    "title",
                    "file_path",
                    "created_date",
                    "modified_date",
                    "tags",
                    "wikilinks",
                    "heading",
                    "level",
                    "section_id",
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "qdrant_url": self.config.qdrant_url,
                "error": str(e),
            }

    def document_exists(self, doc_id: str) -> bool:
        """Check if a document with given ID exists."""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name, ids=[doc_id]
            )
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return False

    def remove_document(self, doc_id: str) -> bool:
        """Remove a specific document by ID."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[doc_id]),
            )
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
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path", match=models.MatchValue(value=file_path)
                        )
                    ]
                ),
                limit=1000,
            )

            doc_ids = [point.id for point in scroll_result[0]]
            if doc_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=doc_ids),
                )
                return len(doc_ids)

            return 0
        except Exception as e:
            logger.error(f"Failed to remove documents by path {file_path}: {e}")
            return 0

    def search_documents(
        self, query: str, k: int = 5, filter_dict: Optional[dict] = None
    ) -> List[Document]:
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

    def search_documents_with_scores(
        self, query: str, k: int = 5, filter_dict: Optional[dict] = None
    ) -> List[Tuple[Document, float]]:
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
            return self.vectorstore.similarity_search_with_score(
                query, k=k, filter=filter_dict
            )
        except Exception as e:
            logger.error(f"Search with scores failed: {e}")
            return []

    def get_documents_by_metadata(
        self, filter_dict: dict, limit: int = 100
    ) -> List[Document]:
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
                where=filter_dict, limit=limit, include=["documents", "metadatas"]
            )

            documents = []
            for i, doc_id in enumerate(results.get("ids", [])):
                if i < len(results.get("documents", [])) and i < len(
                    results.get("metadatas", [])
                ):
                    doc = Document(
                        page_content=results["documents"][i],
                        metadata=results["metadatas"][i],
                    )
                    documents.append(doc)

            return documents
        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            return []

    def get_collection_count(self) -> int:
        """Get the total number of documents in the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            return 0
