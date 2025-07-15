#!/usr/bin/env python3
"""
RAG Micro-Agent Main Entry Point

This module provides the main CLI interface for the RAG micro-agent,
implementing the query planner → retriever → response pipeline as specified
in the technical specification.
"""

import argparse
import os
import sys
import json
import logging
from typing import Dict, Any, Optional

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_community.vectorstores import Chroma

from core.query_planner import deconstruct_query
from core.retriever import retrieve_context
from core.embed import llama_embedder
from config import LLMConfig, validate_config


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RAGMicroAgent:
    """Main RAG micro-agent class that orchestrates query processing."""

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
    ):
        """
        Initialize the RAG micro-agent.

        Args:
            config: LLMConfig object, defaults to env configuration if not provided
        """
        self.config = config or LLMConfig.from_env()

        # Validate configuration
        validation = validate_config(self.config)
        if not validation["can_proceed"]:
            raise ValueError(
                "Configuration validation failed: " + ", ".join(validation["issues"])
            )

        if validation["warnings"]:
            for warning in validation["warnings"]:
                logger.warning(warning)

        # Initialize LangChain Chroma vectorstore
        self.vectorstore = Chroma(
            collection_name=self.config.collection_name,
            embedding_function=llama_embedder,
            persist_directory=self.config.db_path,
        )

        logger.info(
            f"Initialized RAG micro-agent with collection: {self.config.collection_name}"
        )

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query through the full RAG pipeline.

        Args:
            user_query: Natural language query from user

        Returns:
            Dictionary containing the context package
        """
        logger.info(f"Processing query: {user_query}")

        try:
            # Step 1: Deconstruct query using query planner
            query_plan = deconstruct_query(user_query)
            logger.info(f"Generated query plan: {json.dumps(query_plan, indent=2)}")

            # Step 2: Execute retrieval using retriever interface
            context_package = retrieve_context(query_plan, self.vectorstore)
            logger.info(f"Retrieved {len(context_package.get('results', []))} results")

            return context_package

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            # Get count via underlying collection
            count = self.vectorstore._collection.count()
            return {
                "collection_name": self.config.collection_name,
                "document_count": count,
                "db_path": self.config.db_path,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}


def run_rag_query(user_query: str, db_path: str = "./data/chroma_db") -> Dict[str, Any]:
    """
    Convenience function to run a single RAG query.

    Args:
        user_query: Natural language query
        db_path: Path to ChromaDB database

    Returns:
        Context package dictionary
    """
    agent = RAGMicroAgent(db_path=db_path)  # pyright: ignore
    return agent.query(user_query)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="RAG Micro-Agent CLI")
    parser.add_argument("query", nargs="?", help="Natural language query to process")
    parser.add_argument(
        "--db-path",
        default="./data/chroma_db",
        help="Path to ChromaDB database (default: ./data/chroma_db)",
    )
    parser.add_argument(
        "--collection",
        default="obsidian_notes",
        help="Collection name (default: obsidian_notes)",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show collection statistics"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--index",
        help="Path to vault directory to index notes from"
    )
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Clear existing collection before indexing"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Create config from arguments via environment variables
        import os

        os.environ["CHROMA_DB_PATH"] = args.db_path
        os.environ["CHROMA_COLLECTION_NAME"] = args.collection
        agent = RAGMicroAgent()

        if args.stats:
            stats = agent.get_collection_stats()
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print(f"Collection: {stats['collection_name']}")
                print(f"Documents: {stats['document_count']}")
                print(f"Database: {stats['db_path']}")
            return

        if args.index:
            result = agent.index_vault(args.index, reset=args.reset)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                status = "✅ Completed" if result["status"] == "completed" else "❌ Failed"
                print(f"{status}")
                print(f"Files processed: {result['files_processed']}/{result['files_found']}")
                print(f"Documents added: {result['documents_added']}")
                if result["errors"]:
                    print(f"Errors: {len(result['errors'])}")
                    for error in result["errors"]:
                        print(f"  - {error}")
                if result["elapsed_time"] > 0:
                    print(f"Time elapsed: {result['elapsed_time']:.2f}s")
            return

        if not args.query:
            parser.error("Query is required unless --stats or --index is used")

        # Process the query
        result = agent.query(args.query)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Query: {args.query}")
            print(f"Found {len(result.get('results', []))} results:")
            print()

            for i, item in enumerate(result.get("results", []), 1):
                print(f"{i}. {item.get('title', 'Unknown')}")
                if "heading" in item:
                    print(f"   Section: {item['heading']}")
                if "tags" in item and item["tags"]:
                    print(f"   Tags: {', '.join(item['tags'])}")
                if "content" in item:
                    content = (
                        item["content"][:200] + "..."
                        if len(item["content"]) > 200
                        else item["content"]
                    )
                    print(f"   Content: {content}")
                print()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
