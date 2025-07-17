"""
Tests for user query embedding and vectorization.
"""

import pytest
from src.core.query_planner import deconstruct_query
from config import get_embedding_function, LLMConfig


class TestQueryEmbedding:
    """Test user query string vectorization for similarity search."""

    def test_user_query_vectorization(self):
        """Test user query string → embedding vector using configured model."""
        # Get the configured embedding function
        try:
            embedder = get_embedding_function()
        except RuntimeError as e:
            pytest.skip(f"Embedding model not available: {e}")

        # Test with a simple query
        query = "find notes about security threats"

        # Get embedding
        embedding = embedder.embed_query(query)

        # Verify embedding is a list/vector
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, (int, float)) for x in embedding)

    def test_embedding_dimensions_match_model(self):
        """Verify embedding dimensions match model configuration."""
        try:
            embedder = get_embedding_function()
        except RuntimeError as e:
            pytest.skip(f"Embedding model not available: {e}")

        config = LLMConfig.from_env()
        expected_dim = config.qdrant_vector_size

        # Test with a sample query
        query = "test query for dimensions"
        embedding = embedder.embed_query(query)

        # Verify dimensions match configuration
        assert len(embedding) == expected_dim
