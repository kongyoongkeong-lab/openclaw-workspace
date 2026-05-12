#!/usr/bin/env python3
"""
Vector Ingestion Pipeline for PDF Worker
Chunks PDF pages → Generates embeddings → Upserts to Qdrant
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Dependencies (install via pnpm if missing)
# pip install qdrant-client pdf2image pillow python-magic pdfminer.six

from qdrant_client import QdrantClient, Models
from qdrant_client.http import models as rest

# Configuration
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "documents"
EMBEDDING_DIM = 768  # qwen3.5 embedding size
EMBEDDING_MODEL = "qwen3.5"  # Ollama model for embeddings
PDF_WORKER_DIR = "/home/jason2ykk/.openclaw/workspace/pdf-worker"
INPUT_DIR = f"{PDF_WORKER_DIR}/input"
COMPLETED_DIR = f"{PDF_WORKER_DIR}/completed"
CACHE_DIR = f"{PDF_WORKER_DIR}/cache"
EMBED_CACHE_DIR = f"{CACHE_DIR}/embeddings"

def get_qdrant_client():
    """Initialize Qdrant client."""
    return QdrantClient(host=QDRANT_URL)

def create_collection(client: QdrantClient):
    """Create Qdrant collection with proper schema."""
    if not client.collection_exists(QDRANT_COLLECTION):
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=rest.VectorParams(
                size=EMBEDDING_DIM,
                distance=rest.Distance.COSINE,
            ),
            sparse_vectors_config=None,
        )
        print(f"✅ Created collection: {QDRANT_COLLECTION}")
    else:
        print(f"✅ Collection exists: {QDRANT_COLLECTION}")

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using qwen3.5."""
    # TODO: Implement Ollama embedding generation
    # For now, use a placeholder - replace with actual Ollama API call
    print(f"⚠️  Placeholder: Embedding generation not yet connected to Ollama")
    # This would call: ollama.embeddings -model qwen3.5 -text "$text"
    return [0.0] * EMBEDDING_DIM  # Placeholder

def chunk_pdf_to_pages(pdf_path: str) -> List[str]:
    """Extract text from PDF and chunk by page."""
    # Use pdfminer or PyMuPDF to extract pages
    # Placeholder - replace with actual PDF parsing
    print(f"⚠️  Placeholder: PDF chunking not yet connected to pdfminer/PyMuPDF")
    return []

def process_pdf(pdf_path: str) -> Optional[Dict]:
    """Process a single PDF: chunk → embed → upsert."""
    print(f"🔄 Processing: {os.path.basename(pdf_path)}")
    
    # Chunk PDF into page texts
    pages = chunk_pdf_to_pages(pdf_path)
    
    if not pages:
        print(f"❌ Could not extract pages from: {pdf_path}")
        return None
    
    embeddings = []
    contexts = []
    
    for i, page_text in enumerate(pages):
        # Generate embedding
        embedding = generate_embedding(page_text)
        embeddings.append(embedding)
        contexts.append(page_text)
    
    if not embeddings:
        print(f"❌ No embeddings generated for: {pdf_path}")
        return None
    
    # Prepare documents for Qdrant
    documents = []
    for i, (embedding, context) in enumerate(zip(embeddings, contexts)):
        doc_id = f"{os.path.basename(pdf_path)}_page{i+1}"
        document = rest.Document(
            id=doc_id,
            vector=embedding,
            payload={
                "source_file": os.path.basename(pdf_path),
                "page": i + 1,
                "created_at": datetime.now().isoformat(),
                "context": context[:1000],  # Truncate for metadata
                "status": "indexed"
            }
        )
        documents.append(document)
    
    # Upsert to Qdrant
    client = get_qdrant_client()
    client.upsert(collection_name=QDRANT_COLLECTION, points=documents)
    
    print(f"✅ Upserted {len(documents)} documents from: {pdf_path}")
    return {
        "pdf": pdf_path,
        "chunks": len(documents),
        "status": "success"
    }

def ingest_directory():
    """Ingest all PDFs from input directory."""
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"⚠️  No PDFs found in {INPUT_DIR}")
        return
    
    print(f"📂 Found {len(pdf_files)} PDFs to process")
    
    client = get_qdrant_client()
    create_collection(client)
    
    results = []
    for pdf_file in pdf_files:
        pdf_path = f"{INPUT_DIR}/{pdf_file}"
        try:
            result = process_pdf(pdf_path)
            results.append(result)
        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")
            results.append({"pdf": pdf_file, "status": "error", "error": str(e)})
    
    return results

def main():
    """Main ingestion pipeline."""
    print("🚀 Vector Ingestion Pipeline")
    print(f"📍 Input directory: {INPUT_DIR}")
    print(f"🧠 Vector DB: {QDRANT_URL}")
    print(f"📐 Embedding dim: {EMBEDDING_DIM}")
    
    results = ingest_directory()
    
    if results:
        successful = sum(1 for r in results if r.get("status") == "success")
        print(f"\n📊 Summary: {successful}/{len(results)} PDFs processed successfully")

if __name__ == "__main__":
    main()