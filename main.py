#!/usr/bin/env python3
"""
RAG Sub-Agent MVP CLI

Minimal CLI for indexing vaults and querying notes.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.query_planner import deconstruct_query
from src.core.retriever import retrieve_context
from src.core.ingestion.vector_manager import VectorStoreManager
from src.core.ingestion.scanner import VaultScanner, ScanOptions
from src.core.ingestion.processor import NoteProcessor
from config import LLMConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RAG Sub-Agent MVP - Index and query your notes"
    )
    parser.add_argument("query", nargs="?", help="Natural language query to search notes")
    parser.add_argument("--index", help="Path to vault directory to index")
    
    args = parser.parse_args()
    
    if args.index:
        index_vault(args.index)
    elif args.query:
        run_query(args.query)
    else:
        parser.print_help()


def index_vault(vault_path: str):
    """Index a vault directory."""
    pass


def run_query(query: str):
    """Run a query against indexed notes."""
    pass


if __name__ == "__main__":
    main()