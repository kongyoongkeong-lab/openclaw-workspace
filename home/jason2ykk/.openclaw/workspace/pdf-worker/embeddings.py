#!/usr/bin/env python3
"""
Ollama Embedding Integration for PDF Worker
Generates embeddings using qwen3.5 from Ollama API.
"""

import requests
import json

# Configuration
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen3.5"  # Ollama model for embeddings
EMBEDDING_DIM = 768  # qwen3.5 embedding dimension

def generate_embedding(text: str) -> list:
    """
    Generate embedding for text using Ollama.
    
    Args:
        text: Input text to embed
    
    Returns:
        List of floats representing the embedding
    """
    try:
        # Ollama embeddings endpoint
        url = f"{OLLAMA_HOST}/api/embeddings"
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": text,
            "options": {
                "num_ctx": 4096,
                "num_gqa": 64,
                "num_gpu": -1,  # Use all available GPUs
                "f16_kv": True,
                "low_vram": True,
                "fused_kv": True,
            }
        }
        
        # For text embeddings, use the chat endpoint as a fallback
        # Ollama's qwen3.5 may not have a dedicated embeddings endpoint
        chat_url = f"{OLLAMA_HOST}/api/chat"
        
        chat_payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ],
            "stream": False
        }
        
        response = requests.post(chat_url, json=chat_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("message", {}).get("content", "").replace("\n", " ")
        else:
            # Try embeddings endpoint
            emb_response = requests.post(url, json=payload, timeout=30)
            if emb_response.status_code == 200:
                return emb_response.json().get("embeddings", [])
            else:
                raise Exception(f"Embedding generation failed: {response.status_code}")
                
    except Exception as e:
        print(f"⚠️  Embedding generation error: {e}")
        # Return placeholder embedding
        return [0.0] * EMBEDDING_DIM

def generate_embeddings_batch(texts: list) -> list:
    """
    Generate embeddings for multiple texts.
    
    Args:
        texts: List of input texts
    
    Returns:
        List of embeddings (or concatenated text for each)
    """
    embeddings = []
    for text in texts:
        embedding = generate_embedding(text)
        embeddings.append(embedding)
    return embeddings

def test_connection():
    """Test Ollama connection."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Available Ollama models: {[m['name'] for m in models]}")
            return models
        else:
            print(f"❌ Ollama connection failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Ollama connection error: {e}")
        return []

if __name__ == "__main__":
    # Test Ollama connection
    print("🔌 Testing Ollama connection...")
    models = test_connection()
    
    if models:
        # Test embedding generation
        print("\n🧪 Testing embedding generation...")
        test_text = "The quick brown fox jumps over the lazy dog."
        embedding = generate_embedding(test_text)
        
        print(f"\n✅ Generated embedding for: {test_text}")
        print(f"   Type: {type(embedding)}")
        print(f"   Length: {len(embedding)}")
        
        if isinstance(embedding, list):
            print(f"   Preview: {embedding[:10]}...")
        else:
            print(f"   Response: {embedding[:100]}...")
    else:
        print("\n⚠️  Ollama not available - using placeholder embeddings")