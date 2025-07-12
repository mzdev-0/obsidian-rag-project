## RAG Micro-Agent: Technical Specification v1

This document outlines the technical implementation details for the RAG micro-agent, based on the v2 PRD.

### 1. `query_planner.py`

This module is responsible for converting a natural language query into a structured, machine-readable plan.

#### **Functions:**

`deconstruct_query(user_query: str, llm_client) -> dict:`
-   **Purpose**: To generate the JSON query plan.
-   **Parameters**:
    -   `user_query`: The raw string input from the user.
    -   `llm_client`: An instantiated client for an LLM (e.g., from LiteLLM, OpenAI, etc.).
-   **Logic**:
    1.  Load the prompt template (see below).
    2.  Inject the `user_query` into the prompt.
    3.  Send the completed prompt to the LLM via the `llm_client`.
    4.  Receive the string response from the LLM.
    5.  **Crucially, parse the JSON string into a Python dictionary.** Implement a retry loop (2-3 attempts) if the LLM output is not valid JSON. If it consistently fails, raise an exception or return a default "semantic only" plan.
-   **Returns**: A Python dictionary matching the query plan structure, e.g., `{"semantic_query": "...", "filters": [...], "response_format": "..."}`.

#### **Core Asset: `QUERY_PLANNER_PROMPT`**

This is the prompt template to be used.

```text
You are a query analysis engine for a personal knowledge management system. Your task is to deconstruct a user's question into a structured JSON object.

# Today's Date: 2025-07-12

# Available Filters
You can build filters using the following fields with ChromaDB operators ('$gt', '$lt', '$in', etc.):
- "created_date", "modified_date" (ISO 8601 datetime string)
- "tags", "wikilinks" (string, use '$in' for list matching)
- "file_path", "heading", "title" (string)
- "level" (integer, heading level from 1-6)

# Response Formats
Choose the most appropriate response format based on the user's query.
- "metadata_only": The default, efficient choice. Use for broad queries ("find notes about...") or when the user wants a list. This provides a set of pointers (ID, Title, Heading, Tags) for the chat LLM to decide if it needs more info.
- "selective_context": The high-precision choice. Use for specific, factual questions ("what did I write about..."). This returns the actual text content of the most relevant sections.

# User Query
"{{user_query}}"

# Your JSON Output
```

### 2. `retriever.py`

This module executes the plan from the Query Planner and returns the final context package.

#### **Functions:**

`retrieve_context(query_plan: dict, collection) -> dict:`
-   **Purpose**: Orchestrate the retrieval, deduplication, and packaging process.
-   **Parameters**:
    -   `query_plan`: The Python dictionary output from `deconstruct_query`.
    -   `collection`: The instantiated ChromaDB collection object.
-   **Logic**:
    1.  Build the `where` filter dictionary from `query_plan['filters']`. Handle the `$and` operator if multiple filters exist. If no filters, this will be an empty dict.
    2.  Execute the query: `results = collection.query(query_texts=[query_plan['semantic_query']], where=where_filter, n_results=20, include=["metadatas", "documents"])`. (Note: `n_results` should be higher than the final desired count to allow for effective deduplication).
    3.  Call `_deduplicate_results(results)` to get a clean list of sections.
    4.  Based on `query_plan['response_format']`, call either `_package_metadata_only(deduped_results)` or `_package_selective_context(deduped_results)`.
-   **Returns**: The final context package as a dictionary.

`_deduplicate_results(results: dict) -> list:`
-   **Purpose**: To remove redundant sections (e.g., child sections when a parent is already included).
-   **Logic**:
    1.  Initialize `final_results = {}` (a dictionary) and `id_list = []`.
    2.  Iterate through the `results['ids']` and `results['metadatas']` lists in their ranked order.
    3.  For each section, extract its `file_path` from the metadata.
    4.  If `file_path` is **not** in `final_results`:
        -   Add the `file_path` as a key and the entire section object (ID, metadata, document) as the value. `final_results[file_path] = section_data`.
        -   Append the section's ID to `id_list`.
-   **Returns**: A list of the values from `final_results`, which is the deduplicated list of sections.

`_package_metadata_only(sections: list) -> dict:`
-   **Purpose**: To format the results into the `metadata_only` package.
-   **Logic**:
    1.  Iterate through the `sections` list.
    2.  For each section, create a dictionary containing only the `id`, `title`, `heading`, and `tags`.
-   **Returns**: A dictionary like `{"results": [...]}`.

`_package_selective_context(sections: list) -> dict:`
-   **Purpose**: To format the results into the `selective_context` package.
-   **Logic**:
    1.  Iterate through the `sections` list.
    2.  For each section, create a dictionary containing the `id`, `title`, and the full `content` (from the `documents` part of the ChromaDB result), and its `metadata`.
-   **Returns**: A dictionary like `{"results": [...]}`.

### 3. `agent.py` (The Final Entry Point)

`run_rag_query(user_query: str) -> dict:`
-   **Purpose**: To provide a single, simple interface to the entire micro-agent.
-   **Logic**:
    1.  Initialize necessary clients (LLM client, ChromaDB client).
    2.  `plan = deconstruct_query(user_query, llm_client)`.
    3.  `context = retrieve_context(plan, chroma_collection)`.
    4.  Return `context`.
-   This function hides all the internal complexity from the parent LLM.
