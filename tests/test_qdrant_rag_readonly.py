#!/usr/bin/env python3
"""
Bootstrap tests for Read-only Qdrant RAG v0.

Safe tests only: no ingestion, no collection mutation, no global RAG enablement.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'runtime', 'rag'))

from qdrant_retriever import QdrantRetriever, ContextManager


class TestQdrantRagReadonlyBootstrap(unittest.TestCase):
    def _retriever_with_mock_client(self, client=None):
        patcher = patch('qdrant_retriever.QdrantClient')
        mock_cls = patcher.start()
        self.addCleanup(patcher.stop)
        mock_cls.return_value = client or Mock()
        return QdrantRetriever(host='localhost', port=6333, collection_name='openclaw_knowledge'), mock_cls.return_value

    def test_query_points_used_instead_of_search(self):
        client = Mock()
        client.query_points.return_value = Mock(points=[])
        retriever, client = self._retriever_with_mock_client(client)

        result = retriever.retrieve('empty query')

        self.assertEqual(result['status'], 'empty')
        client.query_points.assert_called_once()
        self.assertFalse(getattr(client, 'search', Mock()).called)

    def test_empty_query_returns_clean_empty_result(self):
        client = Mock()
        client.query_points.return_value = Mock(points=[])
        retriever, _ = self._retriever_with_mock_client(client)

        result = retriever.retrieve('empty query')

        self.assertEqual(result, {
            'status': 'empty',
            'query': 'empty query',
            'chunks': [],
            'results': [],
            'chunk_count': 0,
            'total_tokens': 0,
            'message': 'No relevant knowledge found.'
        })

    def test_empty_result_no_hallucination(self):
        client = Mock()
        client.query_points.return_value = Mock(points=[])
        retriever, _ = self._retriever_with_mock_client(client)
        result = retriever.retrieve('empty query')

        self.assertEqual(retriever.answer_from_retrieval(result), 'No relevant knowledge found.')

    def test_retrieval_error_returns_safe_error(self):
        client = Mock()
        client.query_points.side_effect = RuntimeError('backend detail should not be exposed in message')
        retriever, _ = self._retriever_with_mock_client(client)

        result = retriever.retrieve('broken query')

        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['chunks'], [])
        self.assertEqual(result['message'], 'Retrieval failed.')
        self.assertEqual(result['error_type'], 'RuntimeError')
        self.assertNotIn('backend detail', result['message'])

    def test_no_model_call_on_retrieval_error(self):
        client = Mock()
        client.query_points.side_effect = RuntimeError('query failure')
        retriever, _ = self._retriever_with_mock_client(client)
        result = retriever.retrieve('broken query')

        self.assertEqual(retriever.answer_from_retrieval(result), 'Retrieval failed.')

    def test_no_hallucinated_answer_on_empty_chunks(self):
        retriever, _ = self._retriever_with_mock_client(Mock())
        result = {'status': 'empty', 'chunks': []}

        self.assertEqual(retriever.answer_from_retrieval(result), 'No relevant knowledge found.')

    def test_readonly_methods_not_exposed(self):
        for method_name in [
            'upsert', 'delete', 'set_payload', 'delete_payload', 'update_vectors',
            'upload_points', 'recreate_collection', 'delete_collection'
        ]:
            self.assertFalse(hasattr(QdrantRetriever, method_name), method_name)

    def test_forbidden_paths_filtered(self):
        retriever, _ = self._retriever_with_mock_client(Mock())
        for expected in [
            '.env', 'logs/', 'traces/', 'storage/', 'qdrant/',
            'redis/', 'models/', '*.jsonl', 'browser', 'cookies'
        ]:
            self.assertIn(expected, QdrantRetriever.FORBIDDEN_PATHS)

        self.assertTrue(retriever._is_forbidden_path({'path': 'logs/session.log'}))
        self.assertTrue(retriever._is_forbidden_path({'source': 'browser/profile/cookies'}))
        self.assertTrue(retriever._is_forbidden_path({'file': '.env'}))
        self.assertFalse(retriever._is_forbidden_path({'path': 'docs/render_policy.md'}))

    def test_progress_returns_exactly(self):
        retriever, _ = self._retriever_with_mock_client(Mock())

        self.assertEqual(retriever.get_progress_message(), 'Stable. No user action required.')

    def test_limits_and_context_pressure(self):
        client = Mock()
        client.query_points.return_value = Mock(points=[])
        retriever, client = self._retriever_with_mock_client(client)

        self.assertEqual(QdrantRetriever.DEFAULT_TOP_K, 5)
        self.assertEqual(QdrantRetriever.MAX_CHUNK_TOKENS, 800)
        self.assertEqual(QdrantRetriever.MAX_TOTAL_RETRIEVAL_TOKENS, 6000)
        self.assertEqual(ContextManager.get_warning_threshold(), 4000)
        self.assertEqual(ContextManager.get_block_threshold(), 7500)

        retriever.retrieve('cap query', top_k=99)
        self.assertLessEqual(client.query_points.call_args.kwargs['limit'], 5)

        with patch.object(ContextManager, 'is_above_warning_threshold', return_value=True):
            retriever.retrieve('pressure query', top_k=5)
            self.assertLessEqual(client.query_points.call_args.kwargs['limit'], 2)

        with patch.object(ContextManager, 'is_at_block_threshold', return_value=True):
            result = retriever.retrieve('blocked query')
            self.assertEqual(result['status'], 'skipped')


if __name__ == '__main__':
    unittest.main(verbosity=2)
