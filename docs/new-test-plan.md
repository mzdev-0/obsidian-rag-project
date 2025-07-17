# Qdrant Unit Test Implementation Plan

## **Structured Qdrant Unit Test Implementation Checklist**

### **Phase 1: Test Infrastructure Setup**
**File: `tests/unit/conftest.py`**
- [x] **Task 1.1**: Create Qdrant client connection to existing server
- [x] **Task 1.2**: Create test collection fixture using current vector_manager
- [x] **Task 1.3**: **Load real sample notes** from `./data/sample_notes/` directory
- [x] **Task 1.4**: Index real sample notes into test collection

### **Phase 2: Vector Generation Tests**
**File: `tests/unit/test_vector_generation.py`**

**Task 2.1: Test point payload structure**
- [x] **Subtask 2.1.1**: Verify Note → Qdrant point includes all required metadata fields using real sample data
- [x] **Subtask 2.1.2**: Validate data types from actual sample notes (Unix timestamps as int, wikilinks as plain text list)

**Task 2.2: Test wikilink extraction**
- [x] **Subtask 2.2.1**: Verify [[My Note]] → "My Note" (brackets removed) from real sample data
- [x] **Subtask 2.2.2**: Test multiple wikilinks extraction from single real note

### **Phase 3: Query Transformation Tests**
**File: `tests/unit/test_query_transformation.py`**

**Task 3.1: Test temporal filter conversion**
- [x] **Subtask 3.1.1**: Test "last week" → Unix timestamp range using current date
- [x] **Subtask 3.1.2**: Test "this month" → Unix timestamp range

**Task 3.2: Test wikilink filter extraction**
- [x] **Subtask 3.2.1**: Test [[project]] → "project" in Qdrant Filter
- [x] **Subtask 3.2.2**: Test multiple wikilink filters from real sample data

**Task 3.3: Test complex filter combinations**
- [x] **Subtask 3.3.1**: Test temporal + wikilink filters using real sample data
- [x] **Subtask 3.3.2**: Test file path + wikilink filters

### **Phase 4: Query Embedding Tests**
**File: `tests/unit/test_query_embedding.py`**

**Task 4.1: Test user query vectorization**
- [x] **Subtask 4.1.1**: Test user query string vectorization for similarity search
- [x] **Subtask 4.1.2**: Verify embedding dimensions match model configuration

### **Phase 5: Qdrant Client Integration Tests**
**File: `tests/unit/test_qdrant_client.py`**

**Task 5.1: Test filter parameter passing**
- [x] **Subtask 5.1.1**: Test Qdrant Filter object construction matches query plan structure

### **Phase 6: Qdrant Query Execution Tests**
**File: `tests/unit/test_qdrant_queries.py`**

**Task 6.1: Test semantic search with filters**
- [x] **Subtask 6.1.1**: Test vector search + payload filtering returns correct results from real sample data

**Task 6.2: Test metadata-only retrieval**
- [x] **Subtask 6.2.1**: Test search using only payload filters (no semantic search)

**Task 6.3: Test empty results handling**
- [x] **Subtask 6.3.1**: Test graceful handling of zero matches

### **Phase 7: Collection Indexing Tests**
**File: `tests/unit/test_collection_indexing.py`**

**Task 7.1: Test bulk indexing performance**
- [x] **Subtask 7.1.1**: Test all real sample notes indexed efficiently
- [x] **Subtask 7.1.2**: Test memory usage during bulk operations with real data

**Task 7.2: Test incremental indexing**
- [x] **Subtask 7.2.1**: Test adding single note from real samples to existing collection

**Task 7.3: Test large note processing**
- [x] **Subtask 7.3.1**: Test largest sample note processed correctly

## **Test Files to Create**
```
tests/unit/conftest.py
tests/unit/test_vector_generation.py
tests/unit/test_query_transformation.py
tests/unit/test_query_embedding.py
tests/unit/test_qdrant_client.py
tests/unit/test_qdrant_queries.py
tests/unit/test_collection_indexing.py
```

## **Real Sample Data Source**
All tests will use actual markdown files from `./data/sample_notes/` directory, including:
- 2025 Threat Report - Huntress.md
- Any other .md files in the sample_notes directory
- Real wikilinks, dates, and metadata from these files
