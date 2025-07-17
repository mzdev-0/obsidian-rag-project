# Current Query Flow - Mermaid Diagram

## Overview
This document shows the complete flow when a user sends a query via the main.py CLI.

```mermaid
flowchart TD
    A[User Query via CLI] --> B[main.py:run_query]
    B --> C[Initialize LLMConfig]
    C --> D[Initialize VectorStoreManager]
    D --> E[Check Collection Exists]
    E -->|Empty| F[Print "No documents found"]
    E -->|Has Documents| G[deconstruct_query]
    
    G --> H[Query Plan JSON]
    H --> I[retrieve_context]
    
    I --> J[Build Qdrant Filter]
    J --> K[Execute Search]
    K --> L[Process Results]
    
    L --> M[Format Results]
    M --> N[Display to User]
    
    style A fill:#f9f,stroke:#333
    style N fill:#9f9,stroke:#333
```

## Detailed Flow Breakdown

### **Query Processing Pipeline**
1. **CLI Input** → `main.py:run_query(query: str)`
2. **Configuration** → `LLMConfig.from_env()` loads from environment
3. **Vector Store** → `VectorStoreManager(config)` connects to Qdrant
4. **Query Planning** → `deconstruct_query(query)` uses LLM to create JSON plan
5. **Context Retrieval** → `retrieve_context(query_plan, vector_manager)` 
   - Builds Qdrant filters
   - Executes semantic search
   - Packages results
6. **Output** → Simple console formatting

### **Key Components Used**
- **query_planner.py**: LLM-powered query deconstruction
- **retriever.py**: Qdrant search execution
- **vector_manager.py**: Qdrant connection & operations
- **config.py**: Environment-based configuration

### **Data Flow**
```
User Query → JSON Plan → Qdrant Search → Results → Console Output
```

The system is now a complete 2-command CLI that leverages the existing clean architecture while providing a simple interface for the core RAG functionality.