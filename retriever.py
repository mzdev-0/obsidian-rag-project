
from typing import List, Dict, Any

def _build_where_filter(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Builds a ChromaDB 'where' filter from a list of filter conditions.
    Filters are always combined using the '$and' operator.
    """
    if not filters:
        return {}
    
    and_conditions = []
    for f in filters:
        and_conditions.append({f['field']: {f['operator']: f['value']}})
        
    return {"$and": and_conditions}


def _deduplicate_results(results: dict) -> list:
    """
    Removes redundant sections from ChromaDB query results.
    It ensures that for any given note (file_path), only the highest-ranked
    section is kept.
    """
    final_results = {}
    if not results or not results.get('ids') or not results['ids'][0]:
        return []

    # Assuming results are structured as per ChromaDB's output
    ids = results['ids'][0]
    metadatas = results['metadatas'][0]
    documents = results['documents'][0]

    for i, doc_id in enumerate(ids):
        # Gracefully handle cases where metadata might be incomplete
        if i >= len(metadatas) or 'file_path' not in metadatas[i]:
            continue
            
        file_path = metadatas[i]['file_path']
        if file_path not in final_results:
            final_results[file_path] = {
                "id": doc_id,
                "metadata": metadatas[i],
                "document": documents[i] if i < len(documents) else ""
            }
            
    return list(final_results.values())


def _package_metadata_only(sections: list) -> dict:
    """
    Formats the results into the 'metadata_only' package.
    """
    packaged_results = []
    for section in sections:
        tags_list = []
        if 'tags' in section['metadata'] and section['metadata']['tags']:
            tags_list = [tag.strip() for tag in section['metadata']['tags'].split(',') if tag.strip()]

        packaged_results.append({
            "id": section.get('id'),
            "title": section.get('metadata', {}).get('title'),
            "heading": section.get('metadata', {}).get('heading'),
            "tags": tags_list
        })
    return {"results": packaged_results}


def _package_selective_context(sections: list) -> dict:
    """
    Formats the results into the 'selective_context' package.
    """
    packaged_results = []
    for section in sections:
        packaged_results.append({
            "id": section.get('id'),
            "title": section.get('metadata', {}).get('title'),
            "content": section.get('document'),
            "metadata": section.get('metadata')
        })
    return {"results": packaged_results}


def retrieve_context(query_plan: dict, collection) -> dict:
    """
    Orchestrates the retrieval, deduplication, and packaging process.
    """
    where_filter = _build_where_filter(query_plan.get('filters', []))
    
    # Execute the query against the ChromaDB collection
    results = collection.query(
        query_texts=[query_plan['semantic_query']],
        where=where_filter,
        n_results=20,  # Retrieve more results to allow for effective deduplication
        include=["metadatas", "documents"]
    )

    deduped_results = _deduplicate_results(results)

    response_format = query_plan.get('response_format', 'metadata_only')
    if response_format == 'selective_context':
        return _package_selective_context(deduped_results)
    
    return _package_metadata_only(deduped_results)
