#!/usr/bin/env python3
"""
Read-only Qdrant RAG v0 Retriever
Post-H1 conservative upgrade - deterministic runtime mode
"""

import os
import re
import sys
import math
import hashlib
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
except ImportError:
    print("qdrant_client not installed. Install with: pip install qdrant-client")
    sys.exit(1)


class ContextManager:
    """
    Context Manager v1 - Monitors context pressure
    """
    
    @staticmethod
    def get_current_tokens() -> int:
        """Get current token count from active context."""
        try:
            # Read from active session context if available
            context_path = os.environ.get('OPENCLAW_CONTEXT_TOKENS')
            if context_path and os.path.exists(context_path):
                with open(context_path, 'r') as f:
                    content = f.read().strip()
                    if content.isdigit():
                        return int(content)
        except (IOError, ValueError):
            pass
        
        return 0
    
    @staticmethod
    def get_warning_threshold() -> int:
        """Get warning threshold for context pressure."""
        # Default warning at 4000 tokens out of 8000 budget
        return 4000
    
    @staticmethod
    def get_block_threshold() -> int:
        """Get block threshold for context pressure."""
        # Default block at 7500 tokens out of 8000 budget
        return 7500
    
    @staticmethod
    def is_above_warning_threshold() -> bool:
        """Check if current tokens exceed warning threshold."""
        current = ContextManager.get_current_tokens()
        return current > ContextManager.get_warning_threshold()
    
    @staticmethod
    def is_at_block_threshold() -> bool:
        """Check if current tokens exceed block threshold."""
        current = ContextManager.get_current_tokens()
        return current >= ContextManager.get_block_threshold()


class QdrantRetriever:
    """
    Read-only Qdrant Semantic Retriever v0
    
    Features:
    - Read-only access to Qdrant collection
    - Top-k semantic retrieval
    - Token budget enforcement
    - Forbidden path filtering
    - Context pressure awareness
    
    Security:
    - Never writes, upserts, deletes, or mutates Qdrant
    - Filters forbidden paths
    - Never retrieves secrets/tokens/logs
    """
    
    COLLECTION_NAME = "openclaw_knowledge"
    DEFAULT_TOP_K = 5
    MAX_CHUNK_TOKENS = 800
    MAX_TOTAL_RETRIEVAL_TOKENS = 6000
    QUERY_VECTOR_SIZE = 1536
    SCORE_THRESHOLD = 0.05
    PROGRESS_STABLE_MESSAGE = "Stable. No user action required."
    STOPWORDS = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'what',
        'how', 'are', 'was', 'were', 'has', 'have', 'does', 'current'
    }
    
    # Forbidden paths that should never be retrieved
    FORBIDDEN_PATHS = [
        '.env',
        'logs/',
        'traces/',
        'storage/',
        'qdrant/',
        'redis/',
        'models/',
        '*.jsonl',
        'browser',
        'cookies',
    ]
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize read-only Qdrant retriever.
        
        Args:
            host: Qdrant host (defaults to localhost:6333)
            port: Qdrant port
            api_key: Qdrant API key (optional)
            collection_name: Collection name (defaults to openclaw_knowledge)
        """
        self.collection_name = collection_name or self.COLLECTION_NAME
        self.host = host or os.environ.get('QDRANT_HOST', 'localhost')
        self.port = int(os.environ.get('QDRANT_PORT', '6333'))
        self.api_key = api_key or os.environ.get('QDRANT_API_KEY')
        
        # Build Qdrant client without passing a protocol-bearing value to `host`.
        # qdrant-client rejects host="http://localhost:6333"; use `url=` for
        # full URLs or `host=` + `port=` for host/port pairs.
        client_kwargs = {}
        if self.api_key:
            client_kwargs['api_key'] = self.api_key

        if str(self.host).startswith(('http://', 'https://')):
            parsed = urlparse(str(self.host))
            self.host = parsed.hostname or 'localhost'
            self.port = parsed.port or self.port
            client_kwargs['url'] = f"{parsed.scheme}://{self.host}:{self.port}"
        else:
            client_kwargs['host'] = self.host
            client_kwargs['port'] = self.port

        if self.api_key:
            self.client = QdrantClient(**client_kwargs)
        else:
            self.client = QdrantClient(**client_kwargs)
        
        self.logger = self._get_logger()
        
    def _get_logger(self) -> Any:
        """Get logger for external logging (not spam to chat)."""
        try:
            import logging
            logger = logging.getLogger('openclaw.rag.qdrant_retriever')
            logger.setLevel(logging.INFO)
            return logger
        except Exception:
            return None
    
    def _is_forbidden_path(self, point_payload: Dict[str, Any]) -> bool:
        """
        Check if point payload references forbidden paths.
        Rejects retrieval from sensitive locations.
        """
        if not point_payload:
            return False
        
        text_to_check = ""
        
        # Check common fields for paths
        for key in ['path', 'file', 'source', 'url', 'name', 'document_path', 'doc_path', 'filepath']:
            if key in point_payload:
                value = str(point_payload[key]).lower()
                text_to_check += value
        
        # Also check payload text content for concrete sensitive artifacts.
        # Conceptual policy mentions of tokens/logs are allowed in curated docs;
        # actual credentials, browser profiles, cookies, and forbidden path strings are not.
        if 'text' in point_payload:
            text_content = str(point_payload['text']).lower()
            sensitive_patterns = [
                r'https://discord(?:app)?\.com/api/webhooks/',
                r'gh[pousr]_[a-z0-9_]{20,}',
                r'authorization\s*:\s*bearer\s+\S+',
                r'(api[_\s-]?key|secret|token|password)\s*[:=]\s*[\'\"]?\S+',
                r'browser\s+profile',
                r'cookies?\s*[:=]',
                r'\.env\b',
                r'logs/',
                r'traces/',
                r'storage/',
                r'qdrant/',
                r'redis/',
                r'models/',
                r'\.jsonl\b',
            ]
            if any(re.search(pattern, text_content, re.I) for pattern in sensitive_patterns):
                return True
        
        # Check for actual forbidden path prefixes in path-like payload fields only.
        for forbidden in self.FORBIDDEN_PATHS:
            forbidden_lower = forbidden.lower()
            if forbidden_lower == '*.jsonl':
                if '.jsonl' in text_to_check:
                    return True
            elif forbidden_lower in text_to_check:
                return True
        
        return False
    
    def _estimate_chunk_tokens(self, chunk_text: str) -> int:
        """
        Roughly estimate token count for a chunk.
        Simple approximation: 1 token ≈ 4 characters.
        """
        if not chunk_text:
            return 0
        return len(chunk_text) // 4

    def get_progress_message(self) -> str:
        """Return the locked progress render string."""
        return self.PROGRESS_STABLE_MESSAGE

    def _empty_result(self, query: str) -> Dict[str, Any]:
        """Return a deterministic clean-empty retrieval result."""
        return {
            'status': 'empty',
            'query': query,
            'chunks': [],
            'results': [],
            'chunk_count': 0,
            'total_tokens': 0,
            'message': 'No relevant knowledge found.'
        }

    def _safe_error(self, error: Exception) -> Dict[str, Any]:
        """Return a safe retrieval error without leaking details."""
        return {
            'status': 'error',
            'chunks': [],
            'results': [],
            'chunk_count': 0,
            'total_tokens': 0,
            'message': 'Retrieval failed.',
            'error_type': type(error).__name__
        }

    def answer_from_retrieval(self, retrieval_result: Dict[str, Any]) -> str:
        """Never call a model for empty/error retrieval states."""
        if retrieval_result.get('status') == 'error':
            return 'Retrieval failed.'
        if retrieval_result.get('status') == 'empty' or not retrieval_result.get('chunks'):
            return 'No relevant knowledge found.'
        return 'Retrieved relevant knowledge chunks.'

    @classmethod
    def _text_vector(cls, text: str) -> List[float]:
        """Deterministic local lexical vector for v0 curated knowledge retrieval."""
        vector = [0.0] * cls.QUERY_VECTOR_SIZE
        tokens = [
            token for token in re.findall(r"[a-z0-9_]+", (text or '').lower())
            if len(token) > 2 and token not in cls.STOPWORDS
        ]
        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            index = int.from_bytes(digest[:4], 'big') % cls.QUERY_VECTOR_SIZE
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _query_vector(self, query: str) -> List[float]:
        """Build the deterministic read-only query vector."""
        return self._text_vector(query)

    def _extract_points(self, response: Any) -> List[Any]:
        """Support qdrant-client query_points response shapes."""
        if response is None:
            return []
        if hasattr(response, 'points'):
            return list(response.points or [])
        if isinstance(response, list):
            return response
        return []

    def _normalize_points(self, points: List[Any]) -> List[Dict[str, Any]]:
        """Normalize Qdrant points into bounded, filtered chunks."""
        chunks = []
        for point in points:
            payload = getattr(point, 'payload', None) or {}
            score = getattr(point, 'score', 0)

            if self._is_forbidden_path(payload):
                self.logger.warning("Filtered forbidden path in retrieval")
                continue

            text = str(payload.get('text', str(payload)))
            max_chars = self.MAX_CHUNK_TOKENS * 4
            if self._estimate_chunk_tokens(text) > self.MAX_CHUNK_TOKENS:
                text = text[:max_chars]

            chunks.append({
                'text': text,
                'score': score,
                'id': getattr(point, 'id', None),
                'payload': payload
            })
        return chunks
    
    def _trim_to_budget(
        self,
        chunks: List[Dict[str, Any]],
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Trim chunks to stay within token budget.
        Removes lowest-ranked chunks if budget would be exceeded.
        """
        if not chunks:
            return []
        
        # Sort by score descending (keep highest-ranked)
        sorted_chunks = sorted(chunks, key=lambda x: x.get('score', 0), reverse=True)
        
        result = []
        total_tokens = 0
        
        for chunk in sorted_chunks:
            chunk_tokens = self._estimate_chunk_tokens(chunk.get('text', ''))
            
            # Check if adding this chunk would exceed budget
            if total_tokens + chunk_tokens <= budget:
                result.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Budget exceeded, stop including more chunks
                break
        
        return result
    
    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        semantic_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic retrieval from Qdrant collection.
        
        Args:
            query: Semantic search query
            top_k: Number of results to retrieve (default: 5)
            semantic_filter: Optional semantic filter dict
            
        Returns:
            Dict containing:
            - query: Original query
            - results: List of retrieved chunks
            - chunk_count: Number of chunks retrieved
            - total_tokens: Estimated token count
            - status: "success" or error message
            - skipped: True if retrieval was skipped due to context pressure
            
        Raises:
            RuntimeError: If context is at block threshold
        """
        # Check context pressure first
        if ContextManager.is_at_block_threshold():
            return {
                'status': 'skipped',
                'skipped': True,
                'reason': 'Retrieval skipped due to context pressure.',
                'results': [],
                'chunk_count': 0,
                'total_tokens': 0
            }
        
        try:
            # Enforce top_k limit for v0 bootstrap mode.
            effective_top_k = min(max(int(top_k), 0), self.DEFAULT_TOP_K)

            # Reduce top_k if context is at warning level.
            if ContextManager.is_above_warning_threshold():
                effective_top_k = max(1, effective_top_k // 2)

            if not hasattr(self.client, 'query_points'):
                raise RuntimeError('Qdrant query_points unavailable in installed client.')

            # Read-only Query API call. No write/mutation methods are used.
            query_result = self.client.query_points(
                collection_name=self.collection_name,
                query=self._query_vector(query),
                limit=effective_top_k,
                with_payload=True,
                with_vectors=False,
                score_threshold=self.SCORE_THRESHOLD,
                query_filter=semantic_filter
            )

            points = self._extract_points(query_result)
            if not points:
                return self._empty_result(query)

            chunks = self._normalize_points(points)
            if not chunks:
                return self._empty_result(query)
            
            # Trim to token budget
            chunks = self._trim_to_budget(chunks, self.MAX_TOTAL_RETRIEVAL_TOKENS)
            
            # Estimate total tokens
            total_tokens = sum(
                self._estimate_chunk_tokens(c.get('text', '')) 
                for c in chunks
            )
            
            self.logger.info(
                f"Retrieved {len(chunks)} chunks (tokens: {total_tokens}, top_k requested: {effective_top_k})"
            )
            
            return {
                'status': 'success',
                'query': query,
                'chunks': chunks,
                'results': chunks,
                'chunk_count': len(chunks),
                'total_tokens': total_tokens,
                'max_chunk_tokens': self.MAX_CHUNK_TOKENS,
                'max_total_tokens': self.MAX_TOTAL_RETRIEVAL_TOKENS
            }
            
        except Exception as e:
            self.logger.error(f"Retrieval error: {type(e).__name__}")
            return self._safe_error(e)
    
    def search_with_filter(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        top_k: int = DEFAULT_TOP_K
    ) -> Dict[str, Any]:
        """
        Search with optional filters.
        
        Args:
            query: Search query
            filter_dict: Filter conditions (schema: { "field": { "match": "value" } })
            top_k: Number of results
            
        Returns:
            Dict with search results and metadata
        """
        try:
            # Build filter object if provided
            filter_obj = None
            if filter_dict:
                filter_obj = Filter(
                    must=[
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=str(value))
                        )
                        for field, value in filter_dict.items()
                    ]
                )
            
            if not hasattr(self.client, 'query_points'):
                raise RuntimeError('Qdrant query_points unavailable in installed client.')

            effective_top_k = min(max(int(top_k), 0), self.DEFAULT_TOP_K)

            # Perform filtered read-only query
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=self._query_vector(query),
                query_filter=filter_obj,
                limit=effective_top_k,
                with_payload=True,
                with_vectors=False,
                score_threshold=self.SCORE_THRESHOLD
            )
            
            # Process results (reuse retrieval logic)
            chunks = self._normalize_points(self._extract_points(search_result))

            if not chunks:
                return self._empty_result(query)
            
            # Trim to budget
            chunks = self._trim_to_budget(chunks, self.MAX_TOTAL_RETRIEVAL_TOKENS)
            
            total_tokens = sum(
                self._estimate_chunk_tokens(c.get('text', '')) 
                for c in chunks
            )
            
            return {
                'status': 'success',
                'query': query,
                'chunks': chunks,
                'results': chunks,
                'chunk_count': len(chunks),
                'total_tokens': total_tokens
            }
            
        except Exception as e:
            self.logger.error(f"Filtered search error: {type(e).__name__}")
            return self._safe_error(e)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection info (read-only check).
        
        Returns:
            Collection metadata or error info
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                'status': 'success',
                'collection': info
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


def main():
    """Simple CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Read-only Qdrant RAG v0')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--top-k', type=int, default=5, help='Top-k results')
    parser.add_argument('--host', type=str, default='localhost', help='Qdrant host')
    parser.add_argument('--port', type=int, default=6333, help='Qdrant port')
    
    args = parser.parse_args()
    
    # Initialize retriever
    retriever = QdrantRetriever(
        host=args.host,
        port=args.port
    )
    
    # Perform retrieval
    result = retriever.retrieve(
        query=args.query or "default test query",
        top_k=args.top_k
    )
    
    # Output result
    import json
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
