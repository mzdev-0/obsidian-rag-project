# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start & Development Commands

```bash
# Environment setup
export OPENROUTER_API_KEY="your-api-key"
export MODEL_PATH="/path/to/embedding/model.gguf"

# Install dependencies
uv venv && source .venv/bin/activate
uv pip sync

# Run the full system
python main.py  # Populates test DB and runs integration tests
python agent.py  # Run interactive RAG queries

# Testing
python -m unittest discover tests/
python -m unittest tests/test_retriever.py
python -m unittest tests/test_agent.py::TestAgentMilestone1::test_milestone_1_workflow
```

## Architecture Overview

**Specialized RAG micro-agent** with planner-led retrieval. Core workflow:
1. Query decomposition via LLM (`query_planner.py`)
2. Hybrid retrieval (semantic + metadata filtering) via ChromaDB
3. Deduplication of parent/child sections
4. Dual response modes: `metadata_only` (pointers) vs `selective_context` (full content)

## Key Entry Points

- **agent.py** - Main interface: `run_rag_query(user_query, collection=None)`
- **query_planner.py** - LLM-powered query → JSON plan
- **retriever.py** - Orchestrates retrieval and deduplication
- **note.py** - Note parsing and content chunking utilities

## Test Structure

- `TestAgentMilestone1` - End-to-end integration tests with live LLM
- `TestRetriever` - Isolated retrieval logic tests
- `TestNote` - Note parsing and validation
- All tests use temporary ChromaDB instances for isolation

## Important Files

- **main.py**: Integration test runner and test DB population
- **retriever.py:123**: `retrieve_context()` - main retrieval orchestration
- **query_planner.py:45**: `deconstruct_query()` - JSON schema-based query planning
- **note.py:89**: `Note.from_file()` - complete note parsing system