"""
Note ingestion pipeline for the RAG micro-agent.

This package provides the complete pipeline for ingesting markdown files
into the vector store, including scanning, processing, and storage.
"""

from .scanner import VaultScanner, ScanOptions
from .processor import NoteProcessor, ProcessedDocument
from .vector_manager import VectorStoreManager

__all__ = [
    'VaultScanner',
    'ScanOptions', 
    'NoteProcessor',
    'ProcessedDocument',
    'VectorStoreManager'
]