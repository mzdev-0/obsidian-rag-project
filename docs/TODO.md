# RAG Micro-Agent MVP Development Checklist

- [ ] Add batch processing for large vaults
- [ ] Add progress reports during indexing

## Current State Analysis
- ✅ **Core Architecture**: Multi-stage planner-led retrieval system designed
- ✅ **Data Models**: Note parsing, content sections, metadata extraction complete
- ✅ **Embedding Pipeline**: Local embedding models integrated with LangChain-ChromaDB
- ✅ **Retriever Logic**: Deduplication, response packaging, query handling implemented
- ✅ **Test Framework**: Unit tests passing 24/24, integration tests use temporary ChromaDB
- ✅ **Query Planner**: Working with JSON schema validation and fallback
- ✅ **LLM Client**: Configuration abstraction with env variable handling complete
- ✅ **Main Integration**: RAGMicroAgent class fully implemented
- ❌ **Real Data Integration**: No note ingestion pipeline for actual notes
- ❌ **ChromaDB Population**: Collections exist but contain no real note embeddings
- ❌ **Embedding Generation**: Components exist but not connected for vault processing
- ❌ **Integration Tests**: test_agent.py broken (references deleted agent.py)

## MVP Completion Roadmap

### Phase 1: Core System Fixes (Priority: HIGH)
- [x] **Fix Query Planner JSON Schema**
  - [x] Update `SCHEMA_OBJECT` to match ChromaDB's actual operators
  - [x] Add robust JSON parsing with fallback
  - [x] Validate response format matches retriever expectations

- [x] **Change Retriever to Use LangChain Vectorstore**
  - [x] Update retriever.py to accept LangChain Chroma vectorstore
  - [x] Fix metadata format for ChromaDB compatibility
  - [x] Update test setup to use vectorstore instead of raw collection
  - [x] All retriever tests now pass

- [x] **Fix LLM Client Configuration**
  - [x] Standardize environment variable handling (OPENROUTER_API_KEY vs local models)
  - [x] Add local Ollama fallback option for offline usage
  - [x] Create configuration abstraction layer with `config.py`
  - [x] Replace raw ChromaDB collections with LangChain vectorstore everywhere
  - [x] Add comprehensive validation and warnings
  - [x] Provide .env template for easy setup

### Phase 2: Real Data Integration (Priority: HIGH)
**Phase 2.1: Note Ingestion Pipeline**
- [ ] Create note-to-embedding batch processor
- [ ] Implement vault directory scanning and Note parsing
- [ ] Connect local embedding generation with note processing
- [ ] Add progress logging for large vault imports
- [ ] Handle note updates and re-indexing

**Phase 2.2: Embedding Generation System**
- [ ] Build worker to process all notes into embeddings
- [ ] Chunk large notes for better retrieval granularity
- [ ] Preserve metadata during embedding generation
- [ ] Add error handling for malformed notes
- [ ] Implement idempotent re-indexing (handle note changes)

**Phase 2.3: Testing with Real Data**
- [ ] Fix TestAgentMilestone1 to use main.RAGMicroAgent (vs deleted agent.py)
- [ ] Update integration tests to use populated collections
- [ ] Validate end-to-end query→plan→retrieve→package flow with real notes
- [ ] Test semantic search accuracy with actual content
- [ ] Document test data validation procedures

### Phase 3: Environment & Setup (Priority: MEDIUM)
- [ ] **Dependency Management**
  - [ ] Verify uv.lock matches pyproject.toml
  - [ ] Add missing dependencies (chromadb, langchain-community, etc.)
  - [ ] Create requirements.txt for those preferring pip

- [ ] **Configuration Management**
  - [ ] Create `.env.template` with required variables
  - [ ] Add model path configuration for embedding models
  - [ ] Create setup script for first-time users

- [ ] **Documentation**
  - [ ] Update README.md with current setup instructions
  - [ ] Add troubleshooting guide for common issues
  - [ ] Document the query pipeline with examples

### Phase 4: Feature Completion (Priority: MEDIUM)
- [ ] **Response Format Validation**
  - [ ] Ensure metadata_only format returns consistent JSON structure
  - [ ] Validate selective_context includes content and metadata properly
  - [ ] Add response size limits to prevent context overflow

- [ ] **Error Handling & Logging**
  - [ ] Add comprehensive error catching in agent.py
  - [ ] Implement logging configuration throughout modules
  - [ ] Create user-friendly error messages

### Phase 5: Performance & Polish (Priority: LOW)
- [ ] **Query Optimization**
  - [ ] Tune n_results parameter for optimal balance of recall vs processing
  - [ ] Implement query result caching for repeated queries
  - [ ] Add query execution time logging

- [ ] **Configuration Flexibility**
  - [ ] Allow runtime configuration of embedding models
  - [ ] Add persistent database path configuration
  - [ ] Enable switching between local LLM and API modes

## Critical Missing Functionality
- **❌ No embedding generation pipeline** - Tests use temporary DBs, no actual note ingestion
- **❌ No actual ChromaDB setup** - System can't process real notes
- **❌ test_agent.py broken** - Still references deleted agent.py
- **❌ main.py missing collection population** - No way to populate embeddings

## Updated Validation Commands
```bash
# Environment setup
export OPENROUTER_API_KEY="your-key"
export MODEL_PATH="./models/Qwen3-Embedding-0.6B-f16.gguf"

# Check what actually works
python -m unittest tests/test_retriever.py tests/test_query_planner.py tests/test_note.py -v
python -m unittest tests/test_agent.py  # Expected: FAIL due to broken imports
python main.py                          # Expected: FAIL with empty/missing collection
```

## Updated Validation Commands
```bash
# Environment setup
export OPENROUTER_API_KEY="your-key"
export MODEL_PATH="./data/models/Qwen3-Embedding-0.6B-f16.gguf"

# Phase 2 validation (what will work)
python main.py --stats  # Check collection is populated
python main.py "find my notes about RAG"  # Real semantic search
python -m unittest tests/integration/test_agent.py  # Fixed integration tests

# Development workflow
python scripts/ingest_notes.py --vault-dir ./data/sample_notes  # Populate embeddings
python scripts/rebuild_index.py  # Re-index updated notes
```

## Phase 2 Success Criteria
- [ ] test_agent.py refactored to use main.RAGMicroAgent
- [ ] Note ingestion pipeline processes vault directory → embeddings → ChromaDB  
- [ ] Semantic search returns accurate results from real note content
- [ ] All integration tests pass with populated database
- [ ] CLI supports vault indexing commands
- [ ] Re-indexing handles note updates and additions
- [ ] Large vault processing includes progress reporting
