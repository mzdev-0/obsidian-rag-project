## RAG Sub-Agent: Technical Specification v2 - Qdrant Edition

This document outlines the technical implementation details for the Qdrant-powered RAG sub-agent, updated from the v2 PRD.

### 1. `query_planner.py`

This module is responsible for converting natural language queries into structured Qdrant-compatible plans using OpenAI-compatible LLM endpoints. Now supports complex temporal and relational filtering via Qdrant's native filter syntax.

#### **Functions:**

`deconstruct_query(user_query: str, model: str = "qwen3:8b", max_retries: int = 3) -> dict:`
-   **Purpose**: To generate Qdrant-compatible JSON query plan with native temporal and relational filtering.
-   **Parameters**:
    -   `user_query`: The raw string input from the user.
    -   `model`: LLM model identifier (must be JSON schema-aware).
    -   `max_retries`: Number of retry attempts on JSON parsing failure.
-   **Logic**:
    1.  Load prompt template with current date for temporal understanding.
    2.  Parse temporal expressions ("last week", "this month") into Unix timestamp ranges.
    3.  Generate Qdrant filter structure with `must`, `should`, and `range` conditions.
    4.  Support complex filtering for AND/OR conditions on tags, wikilinks, temporal ranges.
    5.  Return fallback plan if parsing fails.
-   **Returns**: Python dictionary with Qdrant filter structure, search parameters, and response format:
    ```json
    {
        "semantic_search_needed": bool,
        "semantic_query": string, 
        "qdrant_filter": dict,
        "response_format": "metadata_only" | "selective_context",
        "search_params": {"k": int, "score_threshold": float, "group_by": str}
    }
    ```

#### **Key Properties:**
- Uses JSON schema validation for reliable parsing
- Manual fallback parsing for resilience
- Retry mechanism with exponential backoff
- Platform-agnostic (any OpenAI-compatible endpoint)

### 2. `retriever.py`

This module executes Qdrant hybrid queries using native client operations, eliminating the previous two-step process.

#### **Functions:**

`retrieve_context(query_plan: dict, qdrant_client, collection_name: str) -> dict:`
-   **Purpose**: Execute single atomic Qdrant query combining semantic search, complex filtering, and native deduplication.
-   **Parameters**:
    -   `query_plan`: Qdrant-compatible plan from `deconstruct_query`.
    -   `qdrant_client`: Native Qdrant client instance.
    -   `collection_name`: Target Qdrant collection name.
-   **Logic**:
    1.  Build Qdrant `Filter` object from `query_plan["qdrant_filter"]`.
    2.  Execute hybrid search with pre-filtered semantic matching.
    3.  Use native `group_by: "file_path"` for per-file deduplication.
    4.  Handle temporal range queries with integer timestamp filters.
    5.  Return results directly from Qdrant without post-processing.
-   **Returns**: Structured context package with deduplicated section results.

#### **Helper Functions:**
- `_build_qdrant_filter()`: Constructs Qdrant Filter objects with must/should/range conditions
- `_execute_hybrid_search()`: Performs single Qdrant query combining vector search + payload filters
- `_handle_group_by_results()`: Processes Qdrant grouped search results
- `_package_metadata_only()`: Creates metadata-only response from Qdrant results
- `_package_selective_context()`: Creates content response with section content

### 3. `main.py` (The Actual Entry Point)

`RAGMicroAgent` class provides unified interface instead of the removed `agent.py`.

#### **Main Interface:**

```python
agent = RAGMicroAgent()
result = agent.query("find my notes about RAG")
```

`run_rag_query(user_query: str, collection_name: str = "obsidian_notes") -> dict:`:
- Uses Qdrant configuration from `config.py`
- Returns structured context package for LLM consumption
- Returns empty results for missing collections with appropriate feedback
