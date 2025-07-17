"""
Tests for Qdrant client integration and parameter passing.
"""

import pytest
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Range
from src.core.query_planner import deconstruct_query


class TestQdrantClientIntegration:
    """Test Qdrant client parameter passing and integration."""

    def test_filter_parameter_passing(self, vector_store_manager):
        """Test Qdrant Filter object construction matches query plan structure."""
        # Create a sample query plan
        query_plan = {
            "semantic_search_needed": True,
            "semantic_query": "security notes",
            "filters": [
                {"field": "created_date", "operator": "gte", "value": 1704067200},
                {"field": "wikilinks", "operator": "contains", "value": "project"},
            ],
            "response_format": "selective_context",
        }

        # Build Qdrant filter from query plan
        from src.core.retriever import _build_qdrant_filter

        qdrant_filter = _build_qdrant_filter(query_plan["filters"])

        # Verify filter structure
        assert isinstance(qdrant_filter, Filter)
        assert qdrant_filter.must is not None
        assert len(qdrant_filter.must) == 2

        # Verify temporal filter
        temporal_condition = qdrant_filter.must[0]
        assert isinstance(temporal_condition, FieldCondition)
        assert temporal_condition.key == "created_date"
        assert temporal_condition.range.gte == 1704067200

        # Verify wikilink filter
        wikilink_condition = qdrant_filter.must[1]
        assert isinstance(wikilink_condition, FieldCondition)
        assert wikilink_condition.key == "wikilinks"
        assert wikilink_condition.match.any == ["project"]
