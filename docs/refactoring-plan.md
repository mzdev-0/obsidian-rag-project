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
**Status:** ✅ COMPLETED

### Actions Completed:
- ✅ **Deleted** ProcessedDocument class entirely - no deprecation
- ✅ **Deleted** redundant parsing.parse_headings() call from processor.py
- ✅ **Simplified** NoteProcessor to be a thin adapter using ContentSection directly
- ✅ **Removed** all intermediate data transformation layers
- ✅ **Added** ContentSection.to_langchain_document() method for direct conversion
- ✅ **Streamlined** architecture to use pre-parsed content sections

## Phase 3: Build Clean Indexing
**Status:** ✅ COMPLETED

### Actions Completed:
- ✅ **Created** index_vault() method from scratch using new architecture
- ✅ **Deleted** legacy test_runner.py (old indexing attempts)
- ✅ **Implemented** clean, minimal API without legacy support
- ✅ **Used** only VectorStoreManager + Note objects for indexing
- ✅ **Updated** integration tests to use new RAGMicroAgent.index_vault()
- ✅ **Added** comprehensive validation tests for vault indexing

## Phase 4: Aggressive Cleanup
**Status:** ✅ COMPLETED

### Actions Completed:
- ✅ **Deleted** deprecated ContentSection.to_document() method entirely
- ✅ **Deleted** local DocumentData class definition (test-specific)
- ✅ **Deleted** unused imports from parsing.py (duplicate List, field, Union, datetime, Path)
- ✅ **Deleted** commented-out image extraction line from note.py
- ✅ **Deleted** outdated deduplication comments from retriever.py
- ✅ **Standardized** import structure by moving inline collections import to module level
- ⚠️ **Preserved** duplicate extract_wikilinks() in standalone utility (count_wikilink_notes.py) for independence

## Testing Strategy
After each phase:
1. Run unit tests: `python -m unittest tests.unit.test_*.py -v`
2. Run integration tests: `python -m unittest tests.integration.test_*.py -v`
3. **Expect breaking changes** - tests may need updates

## Commit Strategy
- **Small, atomic commits** - each deletion is a commit
- **Breaking changes expected** - focus on final clean state
- **No deprecation warnings** - just delete and replace