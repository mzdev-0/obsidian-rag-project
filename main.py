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
        
        for i, file_path in enumerate(md_files, 1):
            try:
                documents = list(processor.process_file(str(file_path)))
                doc_ids = [doc.metadata["id"] for doc in documents]
                
                all_documents.extend(documents)
                all_doc_ids.extend(doc_ids)
                
                print(f"Processed {i}/{len(md_files)}: {file_path.name} ({len(documents)} documents)")
                
            except Exception as e:
                print(f"⚠️  Skipping {file_path.name}: {e}")
        
        if not all_documents:
            print("❌ No documents could be processed")
            return
            
        # Store in vector store
        vector_manager.store_documents(all_documents, all_doc_ids)
        
        print(f"✅ Complete - Indexed {len(all_documents)} documents from {len(md_files)} files")
        
    except Exception as e:
        print(f"❌ Error indexing vault: {e}")
        sys.exit(1)


def run_query(query: str):
    """Run a query against indexed notes."""
    pass


if __name__ == "__main__":
    main()