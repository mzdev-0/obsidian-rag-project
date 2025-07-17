# MVP CLI Implementation Checklist

## Phase 1: Foundation Setup ⏱️ 15 min
- [x] Create empty main.py file structure
- [x] Add basic imports (argparse, sys, pathlib)
- [x] Set up Python path for src module imports
- [x] Create main() function entry point

## Phase 2: CLI Argument Parsing ⏱️ 10 min
- [x] Add argparse with two mutually exclusive arguments
  - [x] `--index` flag for vault path
  - [x] positional `query` argument for natural language
- [x] Add help text and descriptions
- [x] Test argument parsing with sample inputs

## Phase 3: Core Dependencies Setup ⏱️ 10 min
- [x] Import required core modules:
  - [x] `from src.core.query_planner import deconstruct_query`
  - [x] `from src.core.retriever import retrieve_context`
  - [x] `from src.core.ingestion.vector_manager import VectorStoreManager`
  - [x] `from src.core.ingestion.scanner import VaultScanner`
  - [x] `from src.core.ingestion.processor import NoteProcessor`
  - [x] `from config import LLMConfig`

## Phase 4: Index Vault Function ⏱️ 30 min
- [x] Create `index_vault(vault_path: str)` function
- [x] **Subtask 4.1**: Initialize vector store
  - [x] Create LLMConfig from environment
  - [x] Initialize VectorStoreManager
- [x] **Subtask 4.2**: Scan vault directory
  - [x] Create VaultScanner instance
  - [x] Scan for .md files
  - [x] Count total files found
- [x] **Subtask 4.3**: Process files to documents
  - [x] Create NoteProcessor instance
  - [x] Process each file into LangChain Documents
  - [x] Collect all documents with IDs
- [x] **Subtask 4.4**: Store in vector store
  - [x] Use vector_store_manager.store_documents()
  - [x] Print progress ("Processed X/Y files")
- [x] **Subtask 4.5**: Return basic stats
  - [x] Print final count: "Indexed N documents from M files"

## Phase 5: Query Function ⏱️ 25 min
- [x] Create `run_query(query: str)` function
- [x] **Subtask 5.1**: Initialize vector store
  - [x] Create LLMConfig from environment
  - [x] Initialize VectorStoreManager
- [x] **Subtask 5.2**: Process query
  - [x] Call deconstruct_query(query)
  - [x] Handle query planning errors
- [x] **Subtask 5.3**: Retrieve context
  - [x] Call retrieve_context(query_plan, vector_manager)
  - [x] Handle retrieval errors
- [x] **Subtask 5.4**: Format and display results
  - [x] Print query summary
  - [x] Print each result with title and preview
  - [x] Handle empty results gracefully

## Phase 6: Error Handling ⏱️ 10 min
- [x] Add try/catch blocks for common errors:
  - [x] Vault directory not found
  - [x] No markdown files found
  - [x] Vector store connection issues
  - [x] Query processing failures
- [x] Create user-friendly error messages
- [x] Add sys.exit(1) for fatal errors

## Phase 7: Output Formatting ⏱️ 10 min
- [x] **Indexing output format**:
  - [x] "Indexing [vault_path]..."
  - [x] "Found [N] markdown files"
  - [x] "Processed [X] documents"
  - [x] "✅ Complete" or "❌ Error: [message]"
- [x] **Query output format**:
  - [x] "Query: [user_query]"
  - [x] "Found [N] results:"
  - [x] Numbered list with title and section
  - [x] Content preview (first 100 chars)
  - [x] "No results found" when appropriate

## Phase 8: Integration & Testing ⏱️ 20 min
- [ ] **Test indexing command**:
  - [ ] `python main.py --index ./data/sample_notes`
  - [ ] Verify files are found and processed
  - [ ] Check vector store population
- [ ] **Test query command**:
  - [ ] `python main.py 