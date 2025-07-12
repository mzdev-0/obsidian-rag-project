
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Assuming the retriever module and its functions will be created
try:
    from retriever import retrieve_context, _deduplicate_results, _package_metadata_only, _package_selective_context
except ImportError:
    # Create dummy functions for TDD
    def retrieve_context(query_plan, collection):
        results = collection.query(query_texts=[query_plan['semantic_query']], where=query_plan.get('filters', {}), n_results=20)
        deduped = _deduplicate_results(results)
        if query_plan['response_format'] == 'metadata_only':
            return _package_metadata_only(deduped)
        else:
            return _package_selective_context(deduped)

    def _deduplicate_results(results):
        final_results = {}
        for i, doc_id in enumerate(results['ids'][0]):
            file_path = results['metadatas'][0][i]['file_path']
            if file_path not in final_results:
                final_results[file_path] = {
                    "id": doc_id,
                    "metadata": results['metadatas'][0][i],
                    "document": results['documents'][0][i]
                }
        return list(final_results.values())

    def _package_metadata_only(sections):
        results = []
        for section in sections:
            results.append({
                "id": section['id'],
                "title": section['metadata']['title'],
                "heading": section['metadata']['heading'],
                "tags": section['metadata'].get('tags', '').split(',')
            })
        return {"results": results}

    def _package_selective_context(sections):
        results = []
        for section in sections:
            results.append({
                "id": section['id'],
                "title": section['metadata']['title'],
                "content": section['document'],
                "metadata": section['metadata']
            })
        return {"results": results}


class TestRetriever(unittest.TestCase):

    def setUp(self):
        """Set up mock ChromaDB query results."""
        self.mock_chroma_results = {
            'ids': [['note1.md::H1', 'note1.md::H2', 'note2.md::H1']],
            'metadatas': [[
                {'file_path': 'path/to/note1.md', 'title': 'Note 1', 'heading': 'H1', 'level': 1, 'tags': '#test,#project'},
                {'file_path': 'path/to/note1.md', 'title': 'Note 1', 'heading': 'H2', 'level': 2},
                {'file_path': 'path/to/note2.md', 'title': 'Note 2', 'heading': 'H1', 'level': 1, 'tags': '#test'}
            ]],
            'documents': [
                ['Content for H1 in Note 1.'],
                ['Content for H2 in Note 1.'],
                ['Content for H1 in Note 2.']
            ]
        }
        # The spec says deduplication should keep the FIRST result for a given file_path.
        # Let's adjust the mock data to reflect a parent (less specific) coming first.
        self.mock_chroma_results_for_dedup = {
            'ids': [['note1.md::H1', 'note1.md::H1::H2', 'note2.md::H1', 'note1.md::H1::H2::H3']],
            'metadatas': [[
                {'file_path': 'path/to/note1.md', 'title': 'Note 1', 'heading': 'H1', 'level': 1},
                {'file_path': 'path/to/note1.md', 'title': 'Note 1', 'heading': 'H2', 'level': 2},
                {'file_path': 'path/to/note2.md', 'title': 'Note 2', 'heading': 'H1', 'level': 1},
                {'file_path': 'path/to/note1.md', 'title': 'Note 1', 'heading': 'H3', 'level': 3},
            ]],
            'documents': [
                'Content for H1 in Note 1.',
                'Content for H2 in Note 1.',
                'Content for H1 in Note 2.',
                'Content for H3 in Note 1.'
            ]
        }


    def test_deduplicate_results(self):
        """
        Test that only the first-ranked result for each file_path is kept.
        """
        deduped = _deduplicate_results(self.mock_chroma_results_for_dedup)
        
        # There are 3 sections from 2 unique files. Should return 2 sections.
        self.assertEqual(len(deduped), 2)
        
        # It should keep the first one it sees for each file_path
        final_ids = [d['id'] for d in deduped]
        self.assertIn('note1.md::H1', final_ids)
        self.assertIn('note2.md::H1', final_ids)
        self.assertNotIn('note1.md::H1::H2', final_ids)
        self.assertNotIn('note1.md::H1::H2::H3', final_ids)

    def test_package_metadata_only(self):
        """
        Test the metadata_only packaging format.
        """
        sections = _deduplicate_results(self.mock_chroma_results)
        packaged = _package_metadata_only(sections)

        self.assertIn('results', packaged)
        self.assertEqual(len(packaged['results']), 2)
        
        result1 = packaged['results'][0]
        self.assertEqual(result1['id'], 'note1.md::H1')
        self.assertEqual(result1['title'], 'Note 1')
        self.assertEqual(result1['heading'], 'H1')
        self.assertEqual(result1['tags'], ['#test', '#project'])

    def test_package_selective_context(self):
        """
        Test the selective_context packaging format.
        """
        sections = _deduplicate_results(self.mock_chroma_results)
        packaged = _package_selective_context(sections)

        self.assertIn('results', packaged)
        self.assertEqual(len(packaged['results']), 2)

        result1 = packaged['results'][0]
        self.assertEqual(result1['id'], 'note1.md::H1')
        self.assertEqual(result1['title'], 'Note 1')
        self.assertIn('Content for H1', result1['content'])
        self.assertIn('metadata', result1)
        self.assertEqual(result1['metadata']['level'], 1)

    @patch('retriever._deduplicate_results')
    @patch('retriever._package_metadata_only')
    def test_retrieve_context_metadata_flow(self, mock_package_metadata, mock_deduplicate):
        """
        Test the full retrieve_context flow for a metadata_only request.
        """
        # Arrange
        mock_collection = MagicMock()
        mock_collection.query.return_value = self.mock_chroma_results
        mock_deduplicate.return_value = "deduplicated_results" # Dummy value
        mock_package_metadata.return_value = {"results": "metadata_packaged"} # Dummy value

        query_plan = {
            "semantic_query": "test query",
            "filters": {},
            "response_format": "metadata_only"
        }

        # Act
        final_package = retrieve_context(query_plan, mock_collection)

        # Assert
        mock_collection.query.assert_called_once_with(
            query_texts=['test query'],
            where={},
            n_results=20,
            include=["metadatas", "documents"]
        )
        mock_deduplicate.assert_called_once_with(self.mock_chroma_results)
        mock_package_metadata.assert_called_once_with("deduplicated_results")
        self.assertEqual(final_package, {"results": "metadata_packaged"})

    @patch('retriever._deduplicate_results')
    @patch('retriever._package_selective_context')
    def test_retrieve_context_selective_flow(self, mock_package_selective, mock_deduplicate):
        """
        Test the full retrieve_context flow for a selective_context request.
        """
        # Arrange
        mock_collection = MagicMock()
        mock_collection.query.return_value = self.mock_chroma_results
        mock_deduplicate.return_value = "deduplicated_results" # Dummy value
        mock_package_selective.return_value = {"results": "selective_packaged"} # Dummy value
        
        query_plan = {
            "semantic_query": "test query",
            "filters": [{"field": "level", "operator": "$gt", "value": 0}],
            "response_format": "selective_context"
        }

        # Act
        final_package = retrieve_context(query_plan, mock_collection)

        # Assert
        mock_collection.query.assert_called_once_with(
            query_texts=['test query'],
            where={'$and': [{'level': {'$gt': 0}}]},
            n_results=20,
            include=["metadatas", "documents"]
        )
        mock_deduplicate.assert_called_once_with(self.mock_chroma_results)
        mock_package_selective.assert_called_once_with("deduplicated_results")
        self.assertEqual(final_package, {"results": "selective_packaged"})

if __name__ == '__main__':
    unittest.main()
