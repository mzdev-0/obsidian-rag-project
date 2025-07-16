# RAG Micro-Agent Refactoring Plan

## Overview
Clean-slate refactoring to eliminate architectural redundancies. **No backward compatibility maintained** - focus on readable, traversable codebase.

## Phase 1: Burn Down Vector Store Layer
**Status:** ✅ COMPLETED

### Actions Completed:
- ✅ **Enhanced** VectorStoreManager with complete search interface (semantic + metadata)
- ✅ **Replaced** direct Chroma instantiation in main.py with VectorStoreManager
- ✅ **Updated** retriever.py to use VectorStoreManager exclusively
- ✅ **Removed** all direct _collection access and fallback mechanisms
- ✅ **Updated** RAGMicroAgent.query() to use vector_manager instead of vectorstore

## Phase 2: Eliminate Redundant Parsing
**Status:** Pending

### Actions:
- **Delete** ProcessedDocument class entirely - no deprecation
- **Delete** redundant parsing.parse_headings() call from processor.py
- **Simplify** NoteProcessor to be a thin adapter using ContentSection directly
- **Remove** all intermediate data transformation layers

## Phase 3: Build Clean Indexing
**Status:** Pending

### Actions:
- **Create** index_vault from scratch using new architecture
- **Delete** any old indexing attempts
- **Implement** clean, minimal API without legacy support
- **Use** only VectorStoreManager + Note objects

## Phase 4: Aggressive Cleanup
**Status:** Pending

### Actions:
- **Delete** duplicate extract_wikilinks() function entirely
- **Delete** unused imports without checking for usage
- **Delete** test-specific ContentSection class
- **Delete** any commented-out or legacy code
- **Delete** old interfaces without preservation

## Testing Strategy
After each phase:
1. Run unit tests: `python -m unittest tests.unit.test_*.py -v`
2. Run integration tests: `python -m unittest tests.integration.test_*.py -v`
3. **Expect breaking changes** - tests may need updates

## Commit Strategy
- **Small, atomic commits** - each deletion is a commit
- **Breaking changes expected** - focus on final clean state
- **No deprecation warnings** - just delete and replace