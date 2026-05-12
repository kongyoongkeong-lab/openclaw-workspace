#!/usr/bin/env python3
"""
Semantic Search API for PDF Worker
Retrieves relevant documents from Qdrant based on user queries.
"""

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from typing import List, Dict, Optional

# Configuration
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "documents"
TOP_K = 5  # Number of results to return
EMBEDDING_DIM = 768

def get_client():
    return QdrantClient(host=QDRANT_URL)

def query(query_text: str, top_k: int = TOP_K) -> Dict:
    """
    Perform semantic search on user query.
    
    Args:
        query_text: User question or search query
        top_k: Number of top results to return
    
    Returns:
        Dict with query, matches, and context snippets
    """
    client = get_client()
    
    # TODO: Generate embedding for query_text using Ollama/qwen3.5
    # embedding = client.get_embeddings(model="qwen3.5", text=query_text)
    # Placeholder for now
    embedding = [0.0] * EMBEDDING_DIM
    
    search_result = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=top_k,
        query_filter=None,
        with_payload=True,
        with_vector=False,
    )
    
    matches = []
    for hit in search_result:
        matches.append({
            "doc_id": hit.id,
            "source": hit.payload.get("source_file", "unknown"),
            "page": hit.payload.get("page", 1),
            "score": hit.score,
            "context": hit.payload.get("context", "No context available")[:500]
        })
    
    return {
        "query": query_text,
        "count": len(matches),
        "matches": matches
    }

def query_with_filter(query_text: str, status: str = "indexed", top_k: int = TOP_K) -> Dict:
    """
    Query with metadata filtering.
    
    Args:
        query_text: Search query
        status: Filter by document status (indexed, processing, etc.)
        top_k: Number of results
    
    Returns:
        Filtered search results
    """
    client = get_client()
    
    # Build filter
    filter_expr = rest.FieldCondition(
        key="status",
        match=rest.MatchValue(value=status),
    )
    
    # TODO: Generate query embedding
    embedding = [0.0] * EMBEDDING_DIM
    
    search_result = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=embedding,
        limit=top_k,
        query_filter=filter_expr,
        with_payload=True,
        with_vector=False,
    )
    
    matches = []
    for hit in search_result:
        matches.append({
            "doc_id": hit.id,
            "source": hit.payload.get("source_file", "unknown"),
            "page": hit.payload.get("page", 1),
            "status": hit.payload.get("status", "unknown"),
            "score": hit.score,
            "context": hit.payload.get("context", "")[:500]
        })
    
    return {
        "query": query_text,
        "filter": status,
        "count": len(matches),
        "matches": matches
    }

def batch_query(queries: List[str], top_k: int = TOP_K) -> Dict:
    """
    Batch query multiple questions.
    
    Args:
        queries: List of search queries
        top_k: Results per query
    
    Returns:
        Dict mapping each query to its results
    """
    results = {}
    for query in queries:
        results[query] = query(query, top_k)
    return results

def main():
    """Test retrieval interface."""
    client = get_client()
    
    # Verify collection exists
    if not client.collection_exists(QDRANT_COLLECTION):
        print(f"❌ Collection {QDRANT_COLLECTION} does not exist")
        return
    
    print(f"✅ Collection verified: {QDRANT_COLLECTION}")
    
    # Test query
    test_query = "What is the main topic of the document?"
    results = query(test_query)
    
    print(f"\n📝 Test Query: {test_query}")
    print(f"📊 Results: {results['count']} matches")
    
    if results['matches']:
        for match in results['matches']:
            print(f"\n  → {match['source']} (page {match['page']})")
            print(f"    Score: {match['score']:.4f}")
            print(f"    Context: {match['context'][:200]}...")
    else:
        print("⚠️  No results found (expected with placeholder embeddings)")

if __name__ == "__main__":
    main()