
# RAG Micro-Agent for Personal Knowledge Management

**⚠️ WORK IN PROGRESS - NOT YET FUNCTIONAL ⚠️**

This project implements a specialized RAG (Retrieval-Augmented Generation) micro-agent designed to provide a parent Language Model with precise, structured context from a personal knowledge base (like an Obsidian vault).

## Current State
**Individual components work, but full pipeline is incomplete.**
- ✅ Note parsing, metadata extraction
- ✅ Query planner with LLM integration
- ✅ Retriever with deduplication
- ❌ No actual embedding generation
- ❌ No ChromaDB population from real notes
- ❌ Integration tests broken (test_agent.py references deleted agent.py)

## Getting Started

This project uses `uv` for virtual environment and dependency management.

### Prerequisites
- Python 3.10+
- `uv` installed (`pip install uv`)
- Local embedding model (see models/ directory)
- OpenAI-compatible LLM endpoint

### Setup & Installation

1. **Clone and enter the directory:**
   ```bash
   cd obsidian-rag-project
   ```

2. **Create and activate the virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   uv pip sync
   ```

4. **Set up environment variables:**
   ```bash
   export OPENROUTER_API_KEY="your-key"  # or other LLM API
   export MODEL_PATH="./models/Qwen3-Embedding-0.6B-f16.gguf"  # or your model
   # Copy .env.template to .env and fill out
   cp .env.template .env
   ```

### Testing Current Functionality

**Unit tests work:**
```bash
python -m unittest tests/test_note.py tests/test_parsing.py tests/test_query_planner.py tests/test_retriever.py -v
```

**Integration tests broken:**
```bash
python -m unittest tests/test_agent.py  # FAILS - uses deleted agent.py
```

**Main CLI missing population:**
```bash
python main.py "find my notes on RAG"  # Likely fails with empty collection
```

## Development Plan

**⚠️ ACTUAL vs DOCUMENTATION GAPS:**
- **README**: Reflects actual working state
- **Technical Spec**: Updated to actual implementation
- **PRD**: Progress markers updated to reality
- **Roadmap**: Revised with actual progress indicators
- **TODO.md**: The single source of truth for what's working vs what's broken
- **agent.py references**: Removed from all docs (replaced with main.py RAGMicroAgent)
- **test/ folder**: test_agent.py broken and needs refactoring
