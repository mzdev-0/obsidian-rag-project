# Technical Implementation Plan: ChromaDB → Qdrant Migration

Based on the migration-plan.md and supporting documentation, here's the thorough technical implementation plan:

## Phase 1: Foundational Shift — Environment & Configuration

### Dependency Transition
- **Remove**: chromadb>=1.0.15
- **Add**: qdrant-client>=1.9.0, langchain-qdrant>=0.1.0
- **Configuration Update**: Replace CHROMA_DB_PATH with QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME

### Configuration Modernization
- **Network-based**: Move from file-path (./data/chroma_db) to client-server (http://localhost:6333)
- **Connection Parameters**: QDRANT_URL, API keys for cloud deployment
- **Validation**: Ensure reliable Qdrant connection on startup

## Phase 2: Re-architecting Data Handling — Ingestion & Storage

### Robust Indexing Strategy
**Create payload indexes on all key metadata fields:**
- `title` - keyword index for exact title matching
- `file_path` - keyword index for file-specific queries  
- `created_date` - integer index for temporal range queries
- `modified_date` - integer index for last-modified queries
- `tags` - keyword array index for multi-tag filtering
- `wikilinks` - keyword array index for relationship queries
- `heading` - text field for heading-level filtering
- `level` - integer index for section depth queries
- `section_id` - keyword index for unique section identification

### Data Processing Pipeline Refinement
**Update Document metadata schema for Qdrant compatibility:**
- Maintain Note → ContentSection → Document pipeline
- Align Document.metadata with Qdrant payload schema
- Ensure immediate indexing of all metadata fields upon ingestion
- Support array fields (tags, wikilinks) natively in Qdrant

## Phase 3: Enhancing Retrieval Intelligence — The Query Engine

### Evolve the Query Planner
**Revise LLM prompt to generate Qdrant-native query plans:**
- **Filter Structure**: Replace ChromaDB where clauses with Qdrant Filter objects
- **Temporal Parsing**: Convert "last week", "this month" to Unix timestamp ranges
- **Complex Filtering**: Support AND/OR conditions on tags, wikilinks, temporal ranges
- **Qdrant Syntax**: Teach planner Qdrant's must/should/range filter structure

**New query plan format:**
```json
{
  "semantic_search_needed": bool,
  "semantic_query": string,
  "qdrant_filter": {
    "must": [...],
    "should": [...],
    "must_not": [...]
  },
  "response_format": "metadata_only" | "selective_context",
  "search_params": {
    "k": int,
    "score_threshold": float,
    "group_by": "file_path"
  }
}
```

### Delegate Complexity to Database Engine

#### 1. True Hybrid Search Implementation
**Replace current multi-step process:**
- **Before**: Semantic search → Python filtering → Deduplication
- **After**: Single atomic Qdrant query combining vector similarity + payload filters

**Technical changes:**
- Pass semantic vector and metadata filters in single API call
- Qdrant performs pre-filtered vector search
- Eliminate Python post-processing overhead

#### 2. Native Deduplication
**Remove Python-based deduplication:**
- **Delete**: _deduplicate_query_sections() function
- **Replace**: Qdrant's group_by="file_path" during search
- **Result**: Single most relevant section per file, directly from database

**Implementation:**
- Use group_by parameter in Qdrant search
- Set group_size=1 for single result per file
- Eliminate redundant parent/child section handling

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

1. **Configuration Layer**: Update config.py for Qdrant parameters
2. **Vector Store**: Replace VectorStoreManager with QdrantManager
3. **Query Planner**: Update prompt and JSON schema for Qdrant filters
4. **Retriever**: Replace retriever.py with Qdrant-native implementation
5. **Testing**: Update test suite for Qdrant backend
6. **Validation**: Execute target queries and measure improvement

This plan directly implements the architectural evolution described in migration-plan.md, focusing on Qdrant's advanced capabilities rather than database compatibility.