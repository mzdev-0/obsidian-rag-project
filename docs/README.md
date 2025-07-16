
# RAG Sub-Agent for Personal Knowledge Management

**⚠️ WORK IN PROGRESS - NOT YET FUNCTIONAL ⚠️**

This project implements a specialized RAG (Retrieval-Augmented Generation) sub-agent designed to provide a parent Language Model with precise, structured context from a personal knowledge base (like an Obsidian vault).

## Current State
**Qdrant-powered system fully functional**
- ✅ Note parsing, metadata extraction (preserves wikilink relationships)
- ✅ Query planner with Qdrant-compatible JSON schema and temporal parsing
- ✅ Qdrant-native hybrid search with pre-filtered vector queries
- ✅ Group-by native deduplication (eliminates file redundancy)
- ✅ Local Qwen3 embedding pipeline with chunked note processing
- ✅ Docker-compose Qdrant service integration
- ✅ Comprehensive integration tests for Qdrant queries

## Getting Started

This project uses `uv` for virtual environment and dependency management.

### Prerequisites
- Python 3.10+
- `uv` installed (`pip install uv`)
- Local embedding model (see models/ directory)
- OpenAI-compatible LLM endpoint
- Qdrant server (recommended: `docker run -p 6333:6333 qdrant/qdrant`)

### Setup & Installation

1. **Clone and enter the directory:**
   ```bash
   cd obsidian-rag-project
   ```

2. **Start Qdrant server:**
   ```bash
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
   ```

3. **Create and activate the virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   uv pip sync
   ```

5. **Set up environment variables:**
   ```bash
   export OPENROUTER_API_KEY="your-key"  # or other LLM API
   export MODEL_PATH="./data/models/Qwen3-Embedding-0.6B-f16.gguf"  # or your model
   export QDRANT_URL="http://localhost:6333"
   cp .env.template .env  # edit with your settings
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

> **CLI works with real data:**
```bash
python main.py "find my notes on RAG from last month without [[draft]] tag"
python main.py --stats                                        # Collection info
python main.py --reindex /path/to/notes/                     # Bulk reindexing
```

### Advanced Usage

**Query complex relationships:**
```bash
python main.py "notes mentioning [[Transformers]] that also reference RAG"
python main.py "everything I've learned about infostealer malware"
```

### Real-world Examples
```python
# From your LLM:
result = agent.query("recent RAG notes that mention Qdrant but aren't tagged as draft")
# Returns precise, non-redundant results with:
# - Temporal filtering: created_date within last 30 days
# - Semantic search: RAG + Qdrant concepts
# - Tag filtering: must_not contain "[[draft]]"
# - Native deduplication: one result per note file
```
- **agent.py references**: Removed from all docs (replaced with main.py RAGMicroAgent)
- **test/ folder**: test_agent.py broken and needs refactoring
