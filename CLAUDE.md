# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**RAG Micro-Agent for Personal Knowledge Management** - A specialized RAG (Retrieval-Augmented Generation) system designed to provide LLMs with precise, structured context from personal knowledge bases like Obsidian vaults.

**Status**: ⚠️ WORK IN PROGRESS - Individual components work but full pipeline is incomplete

## Core Architecture

The system follows a 3-stage pipeline:
1. **Query Planning** → `query_planner.py` deconstructs natural language into machine-readable JSON plans
2. **Context Retrieval** → `retriever.py` executes plans via ChromaDB vectorstore
3. **Packaging** → Results formatted as context packages for parent LLM consumption

## Development Setup

### Prerequisites
- Python 3.12+
- `uv` (pip install uv)
- OpenRouter API key or local LLM endpoint
- Local embedding model (QWen3-Embedding models in `./data/models/`)

### Environment Setup
```bash
# 1. Create virtual environment
uv venv
source .venv/bin/activate

# 2. Install dependencies
uv pip sync

# 3. Configure environment
cp .env.template .env  # Then edit with your keys/settings
export OPENROUTER_API_KEY="your-key"
export MODEL_PATH="./data/models/Qwen3-Embedding-0.6B-f16.gguf"
```

## Quick Commands

### Testing & Development
```bash
# Run unit tests (working)
python -m unittest tests/unit/test_*.py -v

# Run broken integration tests (needs refactor)
python -m unittest tests/integration/test_agent.py  # FAILS - uses deleted agent.py

# Run specific test
python -m unittest tests.unit.test_parsing -v

# Lint code
ruff check src/

# Format code
ruff format src/

# Type checking
pyright

# Check collection stats
python main.py --stats

# Run RAG query (may fail with empty collection)
python main.py "find my notes on RAG"
```

### Testing Current Functionality
```bash
# Test note parsing
python -c "from src.core.note import Note; note = Note.from_file('data/sample_notes/2025 Threat Report - Huntress.md'); print(note.title, note.wikilinks)"

# Test query planning
python -c "from src.core.query_planner import deconstruct_query; print(deconstruct_query('Recent notes about RAG'))"

# Test retriever framework
python -c "from src.core.retriever import retrieve_context; print('retriever module imported successfully')"
```

## Key Components

### Core Modules (`src/core/`)
- **`main.py`** - CLI entry point orchestrates the full pipeline
- **`query_planner.py`** - Deconstructs natural language to JSON plans using LLM
- **`retriever.py`** - Executes plans against ChromaDB with deduplication
- **`note.py`** - Comprehensive note representation with metadata extraction
- **`parsing.py`** - Markdown parsing for headings, wikilinks, tags, and sections
- **`embed.py`** - LlamaCpp embedding model integration

### Configuration (`config.py`)
- Flexible LLM provider switching (OpenRouter/Ollama)
- Environment-based configuration with validation
- Embedding model selection and validation

## Project Structure

```
obsidian-rag-project/
├── src/                          # Core source code
│   ├── core/
│   │   ├── query_planner.py     # LLM-based query planning
│   │   ├── retriever.py         # Context retrieval logic
│   │   ├── note.py             # Note representation
│   │   └── parsing.py          # Markdown parsing utilities
│   └── utils/                   # Helper utilities
├── tests/                       # Test suite
│   ├── unit/
│   └── integration/
├── data/
│   ├── sample_notes/            # Test markdown files
│   ├── models/                  # Local embedding models
│   └── chroma_db/               # Vector database
├── config.py                   # Configuration management
└── main.py                     # CLI entry point
```

## Current Limitations

- ✅ Note parsing, metadata extraction complete
- ✅ Query planner with LLM integration working  
- ✅ Retriever interface functional
- ❌ No actual embedding generation implemented
- ❌ ChromaDB population from real notes incomplete
- ❌ Integration tests broken (references deleted agent.py)

## Testing Strategy

**Working Tests:** Unit tests for core modules all pass
**Known Issues:** Integration test `test_agent.py` needs refactoring to use `RAGMicroAgent` class from `main.py`

## Dependencies Stack

- **LLM Integration**: OpenAI client, LangChain
- **Vector Storage**: ChromaDB via LangChain
- **Embedding**: LlamaCpp for local embeddings
- **Testing**: Python unittest, pytest-compatible
- **Tooling**: uv (dependency management), ruff (lint/format), pyright (type checking)