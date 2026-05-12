#!/usr/bin/env python3
"""Minimal Vector Ingestion — No sentence-transformers dependency"""

import sys
import json
import os
from qdrant_client import QdrantClient, PointStruct, Distance, VectorParams
from transformers import AutoTokenizer, AutoModel
import numpy as np

def load_embedding_model(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """Load embedding model directly via transformers"""
    print(f"Loading embedding model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    return tokenizer, model

def tokenize_and_embed(texts, tokenizer, model):
    """Tokenize and generate embeddings"""
    print(f"Tokenizing {len(texts)} chunks...")
    encodings = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**encodings)
        embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings.numpy()

import torch

def process_input_directory(input_dir, collection_name="pdf_embeddings"):
    """Process all .txt chunk files in input directory"""
    print(f"Processing directory: {input_dir}")
    
    # Find all .txt chunk files
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    if not txt_files:
        print("❌ No .txt chunk files found")
        return
    
    # Collect all chunks
    chunks = []
    for f in txt_files:
        filepath = os.path.join(input_dir, f)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                # Split into sentences/paragraphs
                sentences = content.replace('\n', '. ')
                chunks.extend([s.strip() for s in sentences.split('.') if s.strip()])
        except Exception as e:
            print(f"⚠️  Error reading {f}: {e}")
    
    print(f"Total chunks collected: {len(chunks)}")
    
    if not chunks:
        print("❌ No valid chunks to embed")
        return
    
    # Initialize Qdrant client
    client = QdrantClient(host="localhost", port=6333)
    
    # Check/create collection
    if not client.collection_exists(collection_name):
        # Create with 384-dim (all-MiniLM)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {collection_name} (384-dim)")
    else:
        # Get existing vector size
        info = client.get_collection(collection_name)
        dim = info.config.params.vectors.size
        print(f"✅ Using existing collection: {collection_name} ({dim}-dim)")
    
    # Load embedding model
    tokenizer, model = load_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
    
    # Generate embeddings
    embeddings = tokenize_and_embed(chunks, tokenizer, model)
    
    # Upsert to Qdrant
    points = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        points.append(PointStruct(
            id=i,
            vector=emb.flatten().tolist(),
            payload={
                "chunk": chunk[:100],  # Preview
                "source": os.path.basename(txt_files[i % len(txt_files)]),
                "status": "indexed"
            }
        ))
    
    client.upsert(collection_name=collection_name, points=points)
    print(f"✅ Indexed {len(points)} chunks into Qdrant")
    
    # Cleanup
    del model, tokenizer, encodings
    print("\n✅ Vector ingestion complete!")

if __name__ == "__main__":
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/Users/jason/Documents/AI_Projects/pdf-worker/output"
    collection_name = sys.argv[2] if len(sys.argv) > 2 else "pdf_embeddings"
    process_input_directory(input_dir, collection_name)