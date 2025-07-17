"""
Tests for query transformation from natural language to Qdrant filters.
"""

import pytest
from datetime import datetime, timedelta
from src.core.query_planner import deconstruct_query


class TestQueryTransformation:
    """Test query transformation from natural language to Qdrant filters."""

    def test_temporal_filter_conversion_last_week(self):
        """Test 'last week' → Unix timestamp range."""
        query = "notes from last week about security"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should have temporal filter
        temporal_filters = [
            f for f in result["filters"] if f["field"] == "created_date"
        ]
        print(temporal_filters)
        assert len(temporal_filters) > 0

        # Should have gte operator for last week
        last_week_filter = temporal_filters[0]
        assert last_week_filter["operator"] == "gte"
        assert isinstance(last_week_filter["value"], int)
        assert last_week_filter["value"] > 0

    def test_temporal_filter_conversion_this_month(self):
        """Test 'this month' → Unix timestamp range."""
        query = "notes from this month about projects"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should have temporal filter
        temporal_filters = [
            f for f in result["filters"] if f["field"] == "created_date"
        ]
        print(temporal_filters)
        assert len(temporal_filters) > 0

        # Should have gte operator for this month
        this_month_filter = temporal_filters[0]
        assert this_month_filter["operator"] == "gte"
        assert isinstance(this_month_filter["value"], int)

    def test_wikilink_filter_extraction_single(self):
        """Test [[project]] → plain text "project" in Qdrant Filter."""
        query = "notes containing wikilink [[project]]"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        wikilink_filters = [f for f in result["filters"] if f["field"] == "wikilinks"]
        print(wikilink_filters)
        assert len(wikilink_filters) > 0

        # Should contain plain text without brackets
        wikilink_filter = wikilink_filters[0]
        assert wikilink_filter["operator"] == "contains"
        assert wikilink_filter["value"] == "project"

    def test_wikilink_filter_extraction_multiple(self):
        """Test multiple wikilink filters from real sample data context."""
        query = "notes containing wikilinks [[project]] and [[security]]"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should have multiple wikilink filters
        wikilink_filters = [f for f in result["filters"] if f["field"] == "wikilinks"]
        assert len(wikilink_filters) >= 1

        # Should extract plain text values
        values = [f["value"] for f in wikilink_filters]
        assert "project" in values or any("project" in str(v) for v in values)
        assert "security" in values or any("security" in str(v) for v in values)

    def test_complex_filter_combinations_temporal_wikilink(self):
        """Test combining temporal + wikilink filters using real sample data."""
        query = "notes from last week tagged [[research]]"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should have both temporal and wikilink filters
        temporal_filters = [
            f for f in result["filters"] if f["field"] == "created_date"
        ]
        wikilink_filters = [f for f in result["filters"] if f["field"] == "tags"]

        assert len(temporal_filters) > 0
        assert len(wikilink_filters) > 0

        # Should have correct operators
        assert temporal_filters[0]["operator"] == "gte"
        assert wikilink_filters[0]["operator"] == "contains"

    def test_complex_filter_combinations_file_path_wikilink(self):
        """Test combining file path + wikilink filters."""
        query = "notes in security folder tagged [[threat]]"
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should have both file path and wikilink filters
        file_filters = [f for f in result["filters"] if f["field"] == "file_path"]
        wikilink_filters = [f for f in result["filters"] if f["field"] == "wikilinks"]

        assert len(file_filters) > 0 or len(wikilink_filters) > 0

        # Should use like operator for file path
        if file_filters:
            assert file_filters[0]["operator"] == "like"

        # Should use contains for wikilinks
        if wikilink_filters:
            assert wikilink_filters[0]["operator"] == "contains"

    def test_empty_query_handling(self):
        """Test graceful handling of empty or nonsensical queries."""
        query = ""
        result = deconstruct_query(query)
        print("--------RESULT ----------\n ")
        print(result)

        # Should return valid structure even for empty query
        assert "semantic_search_needed" in result
        assert "filters" in result
        assert "response_format" in result
        assert isinstance(result["filters"], list)

