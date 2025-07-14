# RAG Micro-Agent MVP Development Checklist

## Current State Analysis
- ✅ **Core Architecture**: Multi-stage planner-led retrieval system designed
- ✅ **Data Models**: Note parsing, content sections, metadata extraction complete
- ✅ **Embedding Pipeline**: Local embedding models integrated with LangChain-ChromaDB
- ✅ **Retriever Logic**: Deduplication, response packaging, query handling implemented
- ✅ **Test Framework**: Integration tests with temporary ChromaDB instances
- ❌ **Query Planner**: Draft exists but needs validation and JSON schema fixes  
- ❌ **End-to-End Integration**: Main.py doesn't match retriever interface
- ❌ **Environment Setup**: Configuration management and dependency validation needed

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

### Phase 2: Validation & Testing (Priority: HIGH)
- [ ] **Fix Test Failures**
  - [ ] Run full test suite: `python -m unittest discover tests/`
  - [ ] Debug retriever.py query vs get path logic
  - [ ] Validate deduplication behavior for both semantic and metadata searches

- [ ] **Integration Testing**
  - [ ] Fix TestAgentMilestone1 to use temporary ChromaDB
  - [ ] Test end-to-end query flow: query→plan→retrieve→package
  - [ ] Validate response formats match PRD specifications

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

## Quick Start Validation Commands
```bash
# Environment setup
export OPENROUTER_API_KEY="your-key"
export MODEL_PATH="./models/Qwen3-Embedding-0.6B-f16.gguf"

# Full system test
python main.py

# Individual component tests
python -m unittest tests/test_retriever.py -v
python -m unittest tests/test_agent.py::TestAgentMilestone1::test_milestone_1_workflow -v

# Manual query testing
python agent.py
```

## Success Criteria Checklist
- [ ] All existing tests pass
- [ ] Query planner produces valid JSON for all query types
- [ ] Retriever correctly processes both semantic and metadata queries
- [ ] Response formats match PRD specifications exactly
- [ ] System handles missing collections gracefully
- [ ] End-to-end integration tests pass with temporary databases
- [ ] Documentation accurately reflects current usage
- [ ] Environment setup works on fresh system

## Post-MVP Features (Future)
- Advanced query operators (regex, fuzzy matching)
- Multi-notebook support
- Query result highlighting/excerpts
- Graph-based relationship discovery
- Export functionality for retrieved contexts