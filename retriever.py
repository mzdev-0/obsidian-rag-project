import logging
from typing import List, Dict, Any

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Helper Functions ---


def _build_where_filter(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds a ChromaDB 'where' filter from a list of filter conditions.
    If multiple filters are provided, they are combined using '$and'.
    """
    if not filters:
        return {}

    if len(filters) == 1:
        f = filters[0]
        return {f["field"]: {f["operator"]: f["value"]}}

    and_conditions = [{f["field"]: {f["operator"]: f["value"]}} for f in filters]

    return {"$and": and_conditions}


def _normalize_get_results(results: dict) -> list:
    """
    Normalizes the flat structure from a ChromaDB 'get' operation
    into a standardized list of section dictionaries.
    """
    normalized_sections = []
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    for i, doc_id in enumerate(ids):
        normalized_sections.append(
            {
                "id": doc_id,
                "document": documents[i] if i < len(documents) else None,
                "metadata": metadatas[i] if i < len(metadatas) else {},
            }
        )
    return normalized_sections


def _deduplicate_query_results(results: dict) -> list:
    """
    Removes redundant sections from ChromaDB 'query' results by keeping only
    the highest-ranked section for any given source file.
    """
    final_results = {}
    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    ids = results["ids"][0]
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    documents = results["documents"][0] if results.get("documents") else []

    for i, doc_id in enumerate(ids):
        metadata = metadatas[i] if i < len(metadatas) else {}
        file_path = metadata.get("file_path")

        if not file_path or file_path in final_results:
            continue

        final_results[file_path] = {
            "id": doc_id,
            "metadata": metadata,
            "document": documents[i] if i < len(documents) else "",
        }

    return list(final_results.values())


# --- Result Packaging Functions ---


def _package_metadata_only(sections: list) -> dict:
    """
    Formats results into the 'metadata_only' package.
    Handles tags as a list, consistent with `note.py`.
    """
    packaged_results = []
    for section in sections:
        # CORRECTED: Assumes 'tags' in metadata is already a list of strings.
        tags_list = section.get("metadata", {}).get("tags", [])

        packaged_results.append(
            {
                "id": section.get("id"),
                "title": section.get("metadata", {}).get("title"),
                "heading": section.get("metadata", {}).get("heading"),
                "tags": tags_list,
            }
        )
    return {"results": packaged_results}


def _package_selective_context(sections: list) -> dict:
    """
    Formats results into the 'selective_context' package.
    """
    packaged_results = []
    for section in sections:
        packaged_results.append(
            {
                "id": section.get("id"),
                "title": section.get("metadata", {}).get("title"),
                "content": section.get("document"),
                "metadata": section.get("metadata"),
            }
        )
    return {"results": packaged_results}


# --- Main Orchestrator ---


def retrieve_context(query_plan: dict, collection) -> dict:
    """
    Orchestrates retrieval and packaging based on the query plan,
    choosing between a semantic 'query' and a metadata 'get'.
    """
    logging.info(
        f"Executing query plan. Semantic search needed: {query_plan.get('semantic_search_needed')}"
    )

    where_filter = _build_where_filter(query_plan.get("filters", []))
    processed_sections = []

    if query_plan.get("semantic_search_needed"):
        logging.info(
            f"Performing semantic QUERY with text: '{query_plan['semantic_query'][:50]}...'"
        )
        results = collection.query(
            query_texts=[query_plan["semantic_query"]],
            where=where_filter,
            n_results=20,
            include=["metadatas", "documents"],
        )
        processed_sections = _deduplicate_query_results(results)

    else:
        logging.info("Performing metadata GET operation.")
        results = collection.get(
            where=where_filter, limit=100, include=["metadatas", "documents"]
        )
        processed_sections = _normalize_get_results(results)

    response_format = query_plan.get("response_format", "metadata_only")
    logging.info(
        f"Packaging {len(processed_sections)} sections for '{response_format}' format."
    )

    if response_format == "selective_context":
        return _package_selective_context(processed_sections)

    return _package_metadata_only(processed_sections)

