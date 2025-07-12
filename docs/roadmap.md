## RAG Micro-Agent: Development Roadmap

This roadmap outlines a three-milestone plan to build, smarten, and stabilize the RAG micro-agent. Each milestone delivers a significant piece of functionality and concludes with a clear definition of what "done" looks like.

---

### **Milestone 1: Building the Core Retrieval Pipeline**

**Goal**: To create a functional, end-to-end pipeline that can execute a query plan and retrieve deduplicated content. This milestone focuses entirely on the `selective_context` path to prove the core mechanics work.

*   **Feature 1: Query Planner Engine**
    *   **Task**: Implement the `deconstruct_query` function in a `query_planner.py` module. This function must take a user query, use an LLM to generate a structured JSON plan, and include robust JSON parsing with a retry-on-failure loop.

*   **Feature 2: Hybrid Search & Deduplication**
    *   **Task**: Implement the core `retrieve_context` function in a `retriever.py` module. This involves two key pieces of logic:
        1.  Dynamically building a ChromaDB `where` filter from the query plan's `filters` list.
        2.  Implementing and applying the `_deduplicate_results` logic to the raw output of the `collection.query` to ensure only the most relevant, non-redundant sections are kept.

*   **Definition of Done**: The system can execute a hard-coded query plan. When `retrieve_context` is called with a plan, it successfully returns a clean Python list of deduplicated section objects, each containing its content and metadata. The core retrieval and processing logic is now validated.

---

### **Milestone 2: Implementing Adaptive Intelligence**

**Goal**: To make the agent "smart" by activating the query planner and enabling the dual-response formatting. The agent will now decide *how* to answer.

*   **Feature 1: Intelligent Response Formatting**
    *   **Task**: Implement the two packaging functions in `retriever.py`: `_package_metadata_only` and `_package_selective_context`.
    *   **Task**: Upgrade `retrieve_context` to be the final orchestrator. It must now read the `response_format` from the query plan and use conditional logic to route the deduplicated results to the correct packaging function.

*   **Feature 2: Activating the Live Planner**
    *   **Task**: Create the main `agent.py` module and the primary entry point `run_rag_query(user_query: str)`.
    *   **Task**: This function will now orchestrate the full, live pipeline: it first calls `deconstruct_query` to get a dynamic plan, then immediately passes that plan to `retrieve_context` to get the final, formatted package.

*   **Definition of Done**: The `run_rag_query` function is fully operational. It can autonomously handle a natural language query from start to finish. It correctly chooses the response format, and a query like `"find my notes about RAG"` successfully returns a `metadata_only` package, while `"what did I write about ChromaDB filters?"` returns a `selective_context` package.

---

### **Milestone 3: Hardening and Validation**

**Goal**: To transform the functional agent into a reliable, production-ready tool through comprehensive testing.

*   **Feature 1: Unit Test Coverage**
    *   **Task**: Develop a suite of unit tests for the critical helper functions. This must include tests for the `_build_where_filter` logic, the `_deduplicate_results` algorithm, and the JSON parsing within the query planner (using a mocked LLM).

*   **Feature 2: End-to-End Integration Testing**
    *   **Task**: Implement a set of integration tests that validate the entire workflow defined in `run_rag_query`. These tests should use a dedicated, pre-populated test collection in ChromaDB and validate the final output against the scenarios laid out in the "Project Completion Tests" section of the PRD.

*   **Definition of Done**: The project has a robust test suite that provides confidence in its correctness and allows for future refactoring. The micro-agent is now considered stable, reliable, and ready for integration as a tool in a parent LLM system.
