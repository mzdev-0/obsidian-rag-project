## RAG Micro-Agent: Technical Specification v1

This document outlines the technical implementation details for the RAG micro-agent, based on the v2 PRD.

### 1. `query_planner.py`

This module is responsible for converting a natural language query into a structured, machine-readable plan using OpenAI-compatible LLM endpoints.

#### **Functions:**

`deconstruct_query(user_query: str, model: str = "qwen3:8b", max_retries: int = 3) -> dict:`
-   **Purpose**: To generate the JSON query plan.
-   **Parameters**:
    -   `user_query`: The raw string input from the user.
    -   `model`: LLM model identifier (must be JSON schema-aware).
    -   `max_retries`: Number of retry attempts on JSON parsing failure.
-   **Logic**:
    1.  Load the prompt template with today's date.
    2.  Add user query to prompt.
    3.  Send to LLM endpoint (configurable via OPENROUTER_API_KEY).
    4.  Receive response using JSON Schema validation.
    5.  Fallback to manual JSON parsing if schema validation fails.
    6.  Return fallback plan if all attempts fail.
-   **Returns**: Python dictionary matching the query plan structure with `semantic_search_needed`, `semantic_query`, `filters`, and `response_format` keys.

#### **Key Properties:**
- Uses JSON schema validation for reliable parsing
- Manual fallback parsing for resilience
- Retry mechanism with exponential backoff
- Platform-agnostic (any OpenAI-compatible endpoint)

### 2. `retriever.py`

This module executes the plan from the Query Planner using LangChain's Chroma vectorstore.

#### **Functions:**

`retrieve_context(query_plan: dict, vectorstore) -> dict:`
-   **Purpose**: Orchestrate retrieval and packaging based on the query plan, choosing between semantic `query` and metadata `get`.
-   **Parameters**:
    -   `query_plan`: The Python dictionary output from `deconstruct_query`.
    -   `vectorstore`: LangChain Chroma vectorstore instance.
-   **Logic**:
    1.  Build `where` filter from `query_plan['filters']`.
    2.  If `semantic_search_needed: true`: Use `vectorstore.similarity_search()` with semantic query.
    3.  If `semantic_search_needed: false`: Use underlying Chroma collection's `get()` with metadata filtering.
    4.  Normalize results to consistent format.
    5.  Apply file-based deduplication (keep highest-ranked from each note).
    6.  Package results based on `response_format`.
-   **Returns**: The final context package as a dictionary.

#### **Helper Functions:**
- `_build_where_filter()`: Builds ChromaDB-compatible where clauses
- `_normalize_get_results()`: Normalizes flat chromadb results to object format
- `_deduplicate_query_sections()`: Deduplicates by file_path (was `_deduplicate_results`)
- `_package_metadata_only()`: Creates metadata-only response
- `_package_selective_context()`: Creates content response

### 3. `main.py` (The Actual Entry Point)

`RAGMicroAgent` class provides unified interface instead of the removed `agent.py`.

#### **Main Interface:**

```python
agent = RAGMicroAgent()
result = agent.query("find my notes about RAG")
```

`run_rag_query(user_query: str, db_path: str = "./chroma_db") -> dict:`:
- Convenience function equivalent to above
- Uses configuration from `config.py`
- Returns structured context package for LLM consumption
- Handles missing collections gracefully
