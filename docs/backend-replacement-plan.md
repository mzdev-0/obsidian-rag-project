# Technical Implementation Plan: ChromaDB → Qdrant Migration

Based on the migration-plan.md and supporting documentation, here's the thorough technical implementation plan:

## Phase 1: Foundational Shift — Environment & Configuration ✅ **COMPLETED**

### Dependency Transition
- **Remove**: chromadb>=1.0.15 ✅ **COMPLETED**
- **Add**: qdrant-client>=1.9.0, langchain-qdrant>=0.1.0 ✅ **COMPLETED**
- **Configuration Update**: Replace CHROMA_DB_PATH with QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME ✅ **COMPLETED**

### Configuration Modernization
- **Network-based**: Move from file-path (./data/chroma_db) to client-server (http://localhost:6333) ✅ **COMPLETED**
- **Connection Parameters**: QDRANT_URL, API keys for cloud deployment ✅ **COMPLETED**
- **Validation**: Ensure reliable Qdrant connection on startup ✅ **COMPLETED**

## Phase 2: Re-architecting Data Handling — Drop-in Qdrant Migration

### VectorStoreManager Refactoring
**Modify existing src/core/ingestion/vector_manager.py:**
- **Replace**: Chroma() with QdrantVectorStore.from_existing_collection()
- **Add**: Qdrant payload indexing during initialization
- **Keep**: Same class name, method signatures, and interface
- **Update**: Collection creation with VectorParams for Qdrant

### Metadata Schema Updates
**Modify src/core/ingestion/processor.py:**
- **Update**: Document.metadata to use arrays for tags/wikilinks (Qdrant native)
- **Change**: created_date/modified_date to Unix timestamps (integers)
- **Add**: section_id field for unique identification
- **Maintain**: Same NoteProcessor class and process_note() interface

### Payload Indexing Implementation
**Add to VectorStoreManager.__init__():**
- Create payload indexes on: title, file_path, created_date, modified_date, tags, wikilinks, heading, level, section_id
- Use Qdrant's create_payload_index() for each field
- Configure appropriate index types (keyword, integer, keyword array)

### Data Pipeline Refinement
**Update processor.py _section_to_document():**
- **Change**: tags from comma-separated string to list[str]
- **Change**: wikilinks from comma-separated string to list[str]
- **Change**: created_date/modified_date to int (Unix timestamps)
- **Add**: section_id field for deduplication support

## Phase 3: Enhancing Retrieval Intelligence — Query Engine Refactoring ✅ **COMPLETED**

### Retriever.py Refactoring ✅ **COMPLETED**
**Modified existing src/core/retriever.py:**
- **Replaced**: _build_where_filter() with _build_qdrant_filter() for native Qdrant Filter objects
- **Updated**: retrieve_context() to use QdrantVectorStore.similarity_search() with Filter objects
- **Removed**: _deduplicate_query_sections() function entirely
- **Added**: Qdrant's group_by="file_path" parameter to search calls

### Query Planner Evolution ✅ **COMPLETED**
**Modified src/core/query_planner.py:**
- **Updated**: deconstruct_query() prompt to generate Qdrant Filter objects
- **Changed**: JSON schema from ChromaDB where clauses to Qdrant filter structure
- **Added**: Unix timestamp conversion for temporal queries
- **Maintained**: Same function signature and return format

### True Hybrid Search Implementation ✅ **COMPLETED**
**Modified retrieve_context():**
- **Replaced**: Two-step "search then filter" with single atomic Qdrant query
- **Used**: QdrantVectorStore.similarity_search() with pre-filtered metadata
- **Added**: group_by="file_path" for native deduplication
- **Removed**: All Python-based post-processing and deduplication

### Native Deduplication ✅ **COMPLETED**
**Technical changes:**
- **Deleted**: _deduplicate_query_sections() function
- **Replaced**: Python deduplication with Qdrant's group_by parameter
- **Configured**: group_size=1 for single result per file
- **Result**: Direct database-level deduplication

## Phase 4: Validation & Verification

### Testing Strategy Updates
**Unit Tests:**
- Mock QdrantVectorManager interface
- Test Qdrant filter generation logic
- Validate payload indexing

**Integration Tests:**
- Test true hybrid search (semantic + metadata)
- Validate native group_by deduplication
- Execute complex compound queries

### Target User Query Validation
Execute all 9 target queries from product-requirements.md:
1. "What did I write about machine learning last month?" (temporal + semantic)
2. "Find my notes on attention mechanisms" (semantic)
3. "Show me everything linked to [[Transformers]]" (relationship filtering)
4. "Recent RAG notes that mention ChromaDB" (compound temporal + topical)
5. Complex CVE queries with temporal filtering
6. Multi-criteria recon TTP queries
7. Visual context queries
8. Infostealer malware compilation
9. Draft exclusion queries

### Success Metrics
- **Functional**: All 9 target queries return accurate, non-redundant results
- **Performance**: Complex queries execute via single atomic operation
- **Efficiency**: No Python-level post-processing required
- **Accuracy**: Better precision/recall than ChromaDB for compound queries

## Technical Implementation Sequence

1. **Configuration Layer**: ✅ **COMPLETED** - config.py updated for Qdrant parameters
2. **Vector Store**: Modify VectorStoreManager to use QdrantVectorStore backend
3. **Query Planner**: Update query_planner.py prompt for Qdrant filter generation
4. **Retriever**: Refactor retriever.py for Qdrant-native filtering and deduplication
5. **Processor**: Update processor.py metadata schema for Qdrant payload compatibility
6. **Testing**: Update test suite for Qdrant backend validation
7. **Validation**: Execute target queries and measure improvement

This plan implements the architectural evolution described in migration-plan.md using drop-in Qdrant backend replacement, maintaining existing interfaces and class names.