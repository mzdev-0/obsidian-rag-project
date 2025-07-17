import logging
from typing import List, Dict, Any
from collections import defaultdict
from qdrant_client.http.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
    MatchText,
)

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Helper Functions ---


def _build_qdrant_filter(filters: List[Dict[str, Any]]) -> Filter:
    """
    Builds a Qdrant Filter object from a list of filter conditions.
    Uses Qdrant's native filtering capabilities for optimal performance.
    """
    logger = logging.getLogger(__name__)

    if not filters:
        logger.debug("No filters provided, returning empty filter")
        return Filter()

    logger.debug(f"Building Qdrant filter from {len(filters)} conditions: {filters}")

    conditions = []

    for f in filters:
        field = f["field"]
        operator = f["operator"]
        value = f["value"]

        if operator == "eq":
            conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
        elif operator == "ne":
            # Qdrant doesn't have direct 'not equal', use must_not
            conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
        elif operator == "gt":
            conditions.append(FieldCondition(key=field, range=Range(gt=value)))
        elif operator == "gte":
            conditions.append(FieldCondition(key=field, range=Range(gte=value)))
        elif operator == "lt":
            conditions.append(FieldCondition(key=field, range=Range(lt=value)))
        elif operator == "lte":
            conditions.append(FieldCondition(key=field, range=Range(lte=value)))
        elif operator == "match":
            if isinstance(value, list):
                conditions.append(FieldCondition(key=field, match=MatchAny(any=value)))
            else:
                conditions.append(
                    FieldCondition(key=field, match=MatchValue(value=value))
                )
        elif operator == "contains":
            # For array fields like tags/wikilinks
            if isinstance(value, list):
                conditions.append(FieldCondition(key=field, match=MatchAny(any=value)))
            else:
                conditions.append(
                    FieldCondition(key=field, match=MatchAny(any=[value]))
                )
        elif operator == "like":
            # For partial string matching
            conditions.append(
                FieldCondition(key=field, match=MatchText(text=str(value)))
            )

    if len(conditions) == 1:
        result = Filter(must=conditions)
    else:
        result = Filter(must=conditions)

    logger.debug(f"Qdrant filter result: {result}")
    return result


def _normalize_get_results(results: dict) -> list:
    """
    Normalizes the flat structure from a ChromaDB 'get' operation
    into a standardized list of section dictionaries.
    """
    logger = logging.getLogger(__name__)

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    logger.debug(
        f"Normalizing get results: {len(ids)} IDs, {len(documents)} documents, {len(metadatas)} metadatas"
    )

    normalized_sections = []
    for i, doc_id in enumerate(ids):
        section = {
            "id": doc_id,
            "document": documents[i] if i < len(documents) else None,
            "metadata": metadatas[i] if i < len(metadatas) else {},
        }
        normalized_sections.append(section)
        logger.debug(
            f"Normalized section {i}: ID={doc_id}, metadata_keys={list(section['metadata'].keys())}"
        )

    logger.debug(f"Normalized {len(normalized_sections)} sections from get operation")
    return normalized_sections


# --- Result Packaging Functions ---


def _package_metadata_only(sections: list) -> dict:
    """
    Formats results into the 'metadata_only' package.
    Handles tags as a list, consistent with `note.py`.
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"Packaging {len(sections)} sections as metadata_only")

    packaged_results = []
    for i, section in enumerate(sections):
        tags_list = section.get("metadata", {}).get("tags", [])
        title = section.get("metadata", {}).get("title")
        heading = section.get("metadata", {}).get("heading")

        packaged_result = {
            "id": section.get("id"),
            "title": title,
            "heading": heading,
            "tags": tags_list,
        }
        packaged_results.append(packaged_result)

        logger.debug(
            f"Packaged section {i}: title='{title}', heading='{heading}', tags_count={len(tags_list)}"
        )

    logger.info(f"Packaged {len(packaged_results)} sections as metadata_only")
    return {"results": packaged_results}


def _package_selective_context(sections: list) -> dict:
    """
    Formats results into the 'selective_context' package.
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"Packaging {len(sections)} sections as selective_context")

    packaged_results = []
    for i, section in enumerate(sections):
        title = section.get("metadata", {}).get("title")
        content_length = len(section.get("document", ""))
        metadata_keys = list(section.get("metadata", {}).keys())

        packaged_result = {
            "id": section.get("id"),
            "title": title,
            "content": section.get("document"),
            "metadata": section.get("metadata"),
        }
        packaged_results.append(packaged_result)

        logger.debug(
            f"Packaged section {i}: title='{title}', content_length={content_length}, metadata_keys={metadata_keys}"
        )

    logger.info(f"Packaged {len(packaged_results)} sections as selective_context")
    return {"results": packaged_results}


# --- Main Orchestrator ---


def retrieve_context(query_plan: dict, vector_manager) -> dict:
    """
    Orchestrates retrieval and packaging based on the query plan,
    choosing between a semantic 'query' and a metadata 'get'.
    """
    import time

    logger = logging.getLogger(__name__)

    start_time = time.time()

    logger.info(
        f"Executing query plan. Semantic search needed: {query_plan.get('semantic_search_needed')}"
    )
    logger.debug(f"Full query plan: {query_plan}")

    qdrant_filter = _build_qdrant_filter(query_plan.get("filters", []))

    logger.debug(f"Processed Qdrant filter: {qdrant_filter}")
    processed_sections = []

    if query_plan.get("semantic_search_needed"):
        semantic_query = query_plan["semantic_query"]
        logger.info(
            f"Performing semantic QUERY with text: '{semantic_query[:100]}{'...' if len(semantic_query) > 100 else ''}'"
        )

        search_start = time.time()
        docs = vector_manager.search_documents(
            query=semantic_query, k=20, filter_dict=qdrant_filter
        )
        search_time = time.time() - search_start

        logger.debug(
            f"Semantic search completed in {search_time:.3f}s, retrieved {len(docs)} documents"
        )

        # Convert LangChain documents to our internal format
        processed_sections = []
        for doc_idx, doc in enumerate(docs):
            section = {
                "id": doc.metadata.get("id", str(doc_idx)),
                "document": doc.page_content,
                "metadata": doc.metadata,
            }
            processed_sections.append(section)
            logger.debug(
                f"Processed section {doc_idx}: title='{doc.metadata.get('title', 'N/A')}', content_length={len(doc.page_content)}"
            )

    else:
        logger.info("Performing metadata GET operation.")

        get_start = time.time()
        docs = vector_manager.get_documents_by_metadata(
            filter_dict=qdrant_filter, limit=100
        )
        get_time = time.time() - get_start

        logger.debug(
            f"Metadata GET completed in {get_time:.3f}s, retrieved {len(docs)} documents"
        )

        # Convert LangChain documents to our internal format
        processed_sections = []
        for doc_idx, doc in enumerate(docs):
            section = {
                "id": doc.metadata.get("id", str(doc_idx)),
                "document": doc.page_content,
                "metadata": doc.metadata,
            }
            processed_sections.append(section)
            logger.debug(
                f"Processed section {doc_idx}: title='{doc.metadata.get('title', 'N/A')}', content_length={len(doc.page_content)}"
            )

    response_format = query_plan.get("response_format", "metadata_only")
    total_time = time.time() - start_time

    logger.info(
        f"Packaging {len(processed_sections)} sections for '{response_format}' format (total time: {total_time:.3f}s)"
    )

    if len(processed_sections) == 0:
        logger.warning(f"Zero sections returned for query plan: {query_plan}")
        logger.warning(f"Filter used: {qdrant_filter}")
        logger.warning(
            f"Semantic search: {query_plan.get('semantic_search_needed', False)}"
        )
        if query_plan.get("semantic_search_needed"):
            logger.warning(f"Query text: '{query_plan.get('semantic_query', 'N/A')}'")

    if response_format == "selective_context":
        result = _package_selective_context(processed_sections)
    else:
        result = _package_metadata_only(processed_sections)

    logger.debug(
        f"Final result contains {len(result.get('results', []))} packaged sections"
    )
    return result
