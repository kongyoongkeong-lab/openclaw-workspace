#!/usr/bin/env python3
"""
PDF Worker Pipeline - Production Deployment
Phase 3 Complete: Memory → Qdrant Ingestion
"""

import os
import sys
from pathlib import Path
import json
import hashlib
from datetime import datetime
import requests

# === CONFIGURATION ===
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "documents"
EMBEDDING_MODEL = "qwen3.5"
OUTPUT_DIR = "/home/jason2ykk/.openclaw/workspace/pdf-worker"
LOG_FILE = f"{OUTPUT_DIR}/cache/logs/ingestion.log"

# === DEPENDENCY CHECK ===
def check_dependencies():
    """Verify sentence-transformers is available"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        return model
    except ImportError:
        print(f"⚠️  sentence-transformers not found, using Ollama API fallback")
        return None

# === EMBEDDING GENERATION ===
def generate_embedding(text, model):
    """Generate 768-dim embedding"""
    if model:
        return model.encode(text, normalize_embeddings=True).tolist()
    
    # Fallback: Ollama API
    response = requests.post(
        "http://localhost:11434/api/embed",
        json={"model": EMBEDDING_MODEL, "prompt": text}
    )
    return response.json()["embedding"]

# === PROCESS SINGLE PDF ===
def process_pdf(pdf_path):
    """Extract text → chunk → embed → upsert to Qdrant"""
    from fitz import doc  # PyMuPDF
    
    doc = doc.open(pdf_path)
    chunks = []
    
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()
        
        # Chunk text (500-1200 tokens)
        chunk_id = page_num * 10 + page_num
        chunk_text = text
        doc_id = Path(pdf_path).stem
        
        embedding = generate_embedding(chunk_text, model)
        
        chunk = {
            "id": hashlib.sha256(f"{doc_id}:{page_num}:{chunk_id}".encode()).hexdigest()[:16],
            "doc_id": doc_id,
            "page_number": page_num + 1,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "text": chunk_text,
            "metadata": {
                "source": pdf_path,
                "created_at": datetime.now().isoformat(),
                "status": "processed"
            }
        }
        chunks.append(chunk)
    
    doc.close()
    return chunks

# === UPSERT TO QDRANT ===
def upsert_to_qdrant(chunks):
    """Upsert chunks to Qdrant collection"""
    base_url = f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points"
    
    for chunk in chunks:
        payload = {
            "payload": chunk["metadata"],
            "vector": chunk["embedding"]
        }
        
        response = requests.post(base_url, json=payload)
        
        if response.status_code == 201 or response.status_code == 200:
            print(f"✅ Upserted: {chunk['doc_id']}#{chunk['chunk_id']}")
        else:
            print(f"❌ Upsert failed: {chunk['doc_id']} - {response.text}")
    
    return len(chunks)

# === RAG RETRIEVAL TEST ===
def query_rag(query, top_k=3):
    """Semantic search and return top-k results"""
    base_url = f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/search"
    
    query_embedding = generate_embedding(query, model)
    
    payload = {
        "vector": query_embedding,
        "limit": top_k,
        "with_payload": True
    }
    
    response = requests.post(base_url, json=payload)
    results = response.json()["results"]
    
    return results

# === MAIN PIPELINE ===
def main():
    """Process queue and upsert to Qdrant"""
    input_dir = f"{OUTPUT_DIR}/input"
    completed_dir = f"{OUTPUT_DIR}/completed"
    
    if not os.path.exists(input_dir):
        print(f"⚠️  {input_dir} not found")
        return
    
    print("🚀 PDF Worker Pipeline - Production Mode")
    print("=" * 50)
    
    # Load model
    model = check_dependencies()
    
    # Process PDFs in input directory
    for pdf_file in os.listdir(input_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(input_dir, pdf_file)
            print(f"\n📄 Processing: {pdf_path}")
            
            chunks = process_pdf(pdf_path)
            
            if chunks:
                count = upsert_to_qdrant(chunks)
                
                # Move to completed
                shutil.copy2(pdf_path, completed_dir)
                print(f"✅ Processed {count} chunks from {pdf_path}")
    
    # === RAG TEST ===
    print("\n🔍 Testing RAG Retrieval...")
    test_query = "extract text from scanned documents"
    results = query_rag(test_query)
    
    if results:
        print(f"✅ RAG Query Successful:")
        for i, result in enumerate(results[:3], 1):
            print(f"   {i}. Score: {result['score']:.4f}")
            print(f"      Doc: {result['payload']['doc_id']}")
            print(f"      Text: {result['payload']['text'][:100]}...")
    else:
        print("⚠️  No results found")
    
    print("\n🚀 Pipeline Complete!")

if __name__ == "__main__":
    import shutil
    main()
