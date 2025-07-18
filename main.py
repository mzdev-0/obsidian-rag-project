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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

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
    parser.add_argument(
        "query", nargs="?", help="Natural language query to search notes"
    )
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
    try:
        print(f"Indexing {vault_path}...")

        # Initialize configuration and vector store
        config = LLMConfig.from_env()
        vector_manager = VectorStoreManager(config)

        # Scan for markdown files
        scanner = VaultScanner(ScanOptions())
        md_files = list(scanner.scan_files(vault_path))

        if not md_files:
            print("❌ No markdown files found")
            return

        print(f"Found {len(md_files)} markdown files")

        # Process files to documents
        processor = NoteProcessor()
        all_documents = []
        all_doc_ids = []

        for file_path in md_files:
            try:
                print(f"Indexing: {file_path}")
                documents = list(processor.process_file(str(file_path)))
                doc_ids = [doc.metadata["id"] for doc in documents]

                all_documents.extend(documents)
                all_doc_ids.extend(doc_ids)

            except Exception as e:
                print(f"⚠️  Skipping {file_path}: {e}")

        if not all_documents:
            print("❌ No documents could be processed")
            return

        # Show model info and document count before embedding
        print(
            f"Embedding {len(all_documents)} documents using {os.getenv('MODEL_PATH')}..."
        )

        # Store in vector store with progress
        vector_manager.store_documents(all_documents, all_doc_ids)

        print(
            f"✅ Complete - Indexed {len(all_documents)} documents from {len(md_files)} files"
        )

    except Exception as e:
        print(f"❌ Error indexing vault: {e}")
        sys.exit(1)


def run_query(query: str):
    """Run a query against indexed notes."""
    try:
        print(f"Query: {query}")

        # Initialize configuration and vector store
        config = LLMConfig.from_env()
        vector_manager = VectorStoreManager(config)

        # Check if collection exists
        stats = vector_manager.get_collection_stats()
        if stats["total_documents"] == 0:
            print("❌ No documents found in collection. Run --index first.")
            return

        # Process query
        query_plan = deconstruct_query(query)

        # Retrieve context
        context_package = retrieve_context(query_plan, vector_manager)
        results = context_package.get("results", [])

        if not results:
            print("No results found")
            return

        print(f"Found {len(results)} results:")
        print()

        for i, result in enumerate(results, 1):
            title = result.get("title", "Unknown")
            heading = result.get("heading", "")
            content = result.get("content", "")

            print(f"{i}. {title}")
            if heading:
                print(f"   Section: {heading}")

            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   {preview}")

            print()

    except Exception as e:
        print(f"❌ Error running query: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

