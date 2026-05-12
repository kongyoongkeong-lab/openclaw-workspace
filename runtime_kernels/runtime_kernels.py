# STEP 8: Search Result Cache (Optional - HIGH IMPACT)
# Location: /workspace/cache/search_cache.json

# Initialize cache directory and file
import os
import json
from pathlib import Path

CACHE_PATH = "/workspace/cache/search_cache.json"
MAX_CACHE_SIZE = 100  # Max 100 cached queries
CACHE_TTL = 7 * 24 * 60 * 60  # 7 days in seconds

# Initialize cache file if it doesn't exist
def init_cache():
    cache_dir = Path(CACHE_PATH).parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'w') as f:
            json.dump({}, f, indent=2)

# Load cache
def load_cache():
    init_cache()
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

# Save cache
def save_cache(cache):
    init_cache()
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2)

# Get cached result
def get_cached_result(query):
    cache = load_cache()
    # Normalize query for comparison
    normalized = query.strip().lower()
    return cache.get(normalized)

# Cache search results
def cache_search_result(query, results, source):
    cache = load_cache()
    normalized = query.strip().lower()
    
    # Update cache with new entry
    if normalized not in cache:
        cache[normalized] = {
            'query': query,
            'results': results,
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
    
    # Limit cache size
    if len(cache) > MAX_CACHE_SIZE:
        # Remove oldest entries (simple approach - could use a more sophisticated LRU)
        sorted_cache = sorted(cache.items(), key=lambda x: x[1].get('timestamp', ''))
        keys_to_remove = sorted_cache[:-MAX_CACHE_SIZE]
        for key in keys_to_remove:
            del cache[key]
    
    save_cache(cache)

# STEP 9: Pentagon Agent Routing
# Location: runtime_kernels.py (within search_dispatcher function)

def route_to_agent(task_type):
    """Route tasks to appropriate Pentagon agent."""
    routes = {
        "research": "intel",
        "execution": "ops",
        "communication": "comms",
        "guardian": "sentinel"
    }
    
    return routes.get(task_type, "intel")
