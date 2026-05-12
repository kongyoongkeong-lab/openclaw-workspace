import json
import random
import time
from datetime import datetime
from tavily import TavilyClient

# Initialize Tavily client (using env var or default)
client = TavilyClient(api_key="tavily")

def run_workload(seed=None):
    """Execute the full workload"""
    if seed:
        random.seed(seed)
    
    start = time.time()
    
    # Step 1: Fetch 3 random tech articles
    print(f"[{datetime.now().isoformat()}] Fetching articles...")
    search_results = client.search("technology", max_results=50)
    articles = search_results.get("results", [])[:3]
    
    # Step 2: Process each article
    results = []
    for idx, article in enumerate(articles):
        title = article.get("title", "Untitled")
        
        # Summary - use first 50 words of content
        content = article.get("content", "")[:500]
        words = content.split()
        summary = f"Summary of: {title[:60]}. Content begins: {content[:150]}..."
        
        # Entities - extract from title and content
        title_lower = title.lower()
        entities = []
        for word in ["AI", "ML", "cloud", "security", "IoT", "blockchain", "5G", "VR", "AR", "robot"]:
            if word.lower() in title_lower:
                entities.append(word)
        
        results.append({
            "title": title,
            "url": article.get("url", ""),
            "summary": summary,
            "entities": entities,
            "processing_time_ms": time.time() - start
        })
    
    processing_time = time.time() - start
    return {
        "seed": seed,
        "timestamp": datetime.now().isoformat(),
        "processing_time_seconds": processing_time,
        "articles_count": len(results),
        "results": results
    }

if __name__ == "__main__":
    import sys
    run_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    print(f"\n=== RUN #{run_num} ===")
    result = run_workload()
    print(json.dumps(result, indent=2, default=str))
