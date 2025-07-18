# Detailed Query Flow with Pipes - Function Args & Values

## Complete Query Processing Pipeline with Edge Labels

```mermaid
flowchart TD
    A["find my notes about RAG"] -->|query: str| B[main.py:run_query]
    
    B -->|config = LLMConfig.from_env()| C[Configuration Load]
    C -->|config| D[VectorStoreManager(config)]
    D -->|collection_name: "obsidian_notes"| E[Collection Connection]
    
    E -->|user_query: "find my notes about RAG"| F[deconstruct_query]
    F -->|model: "qwen3:8b", max_retries: 3| G[OpenAI API Call]
    G -->|response_format: JSON_SCHEMA| H[Query Plan JSON]
    
    H -->|query_plan: dict| I[retrieve_context]
    I -->|query_plan: dict, vector_manager: VectorStoreManager| J[_build_qdrant_filter]
    J -->|filters: []| K[Filter Object Creation]
    
    K -->|query: "notes about Retrieval-Augmented Generation", k: 20| L[vector_manager.search_documents]
    L -->|filter: Filter(must=[]), limit: 20| M[Qdrant Hybrid Search]
    
    M -->|semantic_query: "notes about Retrieval-Augmented Generation", filter: Filter| N[Vector Similarity + Metadata]
    N -->|top_k: 20, score_threshold: 0.0| O[Results Collection]
    
    O -->|results: list, response_format: "selective_context"| P[_package_selective_context]
    P -->|sections: list| Q[Context Package]
    
    Q -->|results: list| R[Console Formatting]
    R -->|max_preview: 200 chars| S[User Display]
    
    style A fill:#ff6b6b,stroke:#333
    style M fill:#4ecdc4,stroke:#333
    style S fill:#45b7d1,stroke:#333
```

## Detailed Edge Labels with Function Signatures

### Query Planning Flow
```mermaid
flowchart LR
    A[Raw Query] -->|user_query: str| B[deconstruct_query]
    B -->|model: str = "qwen3:8b"| C[OpenAI Client]
    C -->|response_format: JSON_SCHEMA| D[Query Plan]
    D -->|{
      semantic_search_needed: true,
      semantic_query: str,
      filters: list,
      response_format: str
    }| E[JSON Output]
```

### Search Execution Flow
```mermaid
flowchart LR
    A[Query Plan] -->|query_plan: dict| B[retrieve_context]
    B -->|query_plan: dict, vector_manager: VectorStoreManager| C[_build_qdrant_filter]
    C -->|filters: list[dict]| D[Qdrant Filter Object]
    D -->|filter: Filter, query: str, k: int| E[search_documents]
    E -->|query: str, k: 20, filter_dict: dict| F[similarity_search]
```

### Result Processing Flow
```mermaid
flowchart LR
    A[Search Results] -->|docs: list[Document]| B[retrieve_context]
    B -->|sections: list[dict]| C[_package_selective_context]
    C -->|sections: list, format: str| D[Context Package]
    D -->|{
      results: [
        {
          id: str,
          title: str,
          heading: str,
          content: str
        }
      ]
    }| E[Formatted Output]
```

## Function Call Chain with Arguments

### 1. Entry Point
```
main.py:run_query(query: str = "find my notes about RAG")
```

### 2. Configuration
```
LLMConfig.from_env() → LLMConfig object
├── openrouter_api_key: str (from env)
├── qdrant_url: str (from env)
├── qdrant_collection_name: str = "obsidian_notes"
└── qdrant_vector_size: int = 1024
```

### 3. Vector Store
```
VectorStoreManager(config: LLMConfig)
├── client: QdrantClient(url: str, timeout: 60)
├── collection_name: str = "obsidian_notes"
└── vectorstore: QdrantVectorStore
```

### 4. Query Planning
```
deconstruct_query(
    user_query: str = "find my notes about RAG",
    model: str = "qwen3:8b",
    max_retries: int = 3
) → dict
```

### 5. Filter Construction
```
_build_qdrant_filter(filters: list[dict]) → Filter
├── FieldCondition(key: str, match: MatchValue)
├── Range(gt: int, lt: int)
└── Filter(must: list[Condition])
```

### 6. Search Execution
```
vector_manager.search_documents(
    query: str = "notes about Retrieval-Augmented Generation",
    k: int = 20,
    filter_dict: dict = {}
) → list[Document]
```

### 7. Result Packaging
```
_package_selective_context(sections: list[dict]) → dict
├── results: list[dict]
├── title: str
├── heading: str
└── content: str (truncated to 200 chars)
```

## Data Transformation Values

### Query Plan Example
```json
{
  "semantic_search_needed": true,
  "semantic_query": "notes about Retrieval-Augmented Generation",
  "filters": [],
  "response_format": "selective_context"
}
```

### Search Parameters
- **embedding_dimension**: 1024
- **distance_metric**: COSINE
- **k**: 20 results
- **score_threshold**: 0.0
- **collection**: obsidian_notes

### Result Structure
```json
{
  "results": [
    {
      "id": "uuid-string",
      "title": "RAG Architecture",
      "heading": "Vector Database Setup",
      "content": "The vector database stores embeddings..."
    }
  ]
}
```