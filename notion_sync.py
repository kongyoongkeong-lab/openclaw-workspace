#!/usr/bin/env python3
"""
Notion Sync — fetches Notion pages/databases and stores in Qdrant.
Usage:
  python3 notion_sync.py              # Full sync
  python3 notion_sync.py --status     # Show sync stats
"""
import json
import os
import sys
import time
from urllib.request import Request, urlopen

QDRANT_URL = "http://localhost:6333"
COLLECTION = "pentagon_brain"
CRED_FILE = os.path.expanduser("~/.openclaw/credentials/notion.json")

def load_token():
    if not os.path.exists(CRED_FILE):
        print("❌ Notion token not found. Create ~/.openclaw/credentials/notion.json")
        print("   See NOTION_PROTOCOL.md for setup instructions.")
        sys.exit(1)
    with open(CRED_FILE) as f:
        return json.load(f)["token"]

def fetch_pages(token):
    """Fetch all pages the integration has access to."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    # Search all pages
    req = Request("https://api.notion.com/v1/search", 
                  data=b'{}', headers=headers, method="POST")
    try:
        resp = urlopen(req)
        data = json.loads(resp.read())
        return data.get("results", [])
    except Exception as e:
        print(f"❌ API error: {e}")
        return []

def extract_content(page):
    """Extract title and content from a Notion page."""
    props = page.get("properties", {})
    title = "Untitled"
    for key, val in props.items():
        if val.get("type") == "title":
            parts = val.get("title", [])
            title = "".join(p.get("plain_text", "") for p in parts)
            break
    return {
        "id": page["id"],
        "title": title,
        "url": page.get("url", ""),
        "type": page.get("object", "page"),
        "last_edited": page.get("last_edited_time", ""),
    }

def store_in_qdrant(pages):
    """Store pages in Qdrant vector DB."""
    count = 0
    for page in pages:
        content = extract_content(page)
        # Upsert to Qdrant
        payload = {
            "source": "notion",
            "page_id": content["id"],
            "title": content["title"],
            "url": content["url"],
            "type": content["type"],
            "text": content["title"],
            "timestamp": time.time(),
        }
        # Simple text-based upsert (no embedding - embedding done at query time)
        url = f"{QDRANT_URL}/collections/{COLLECTION}/points"
        body = json.dumps({
            "points": [{
                "id": hash(content["id"]) % (2**63),
                "vector": [0.0] * 384,  # placeholder vector
                "payload": payload
            }]
        }).encode()
        req = Request(url, data=body, method="PUT")
        req.add_header("Content-Type", "application/json")
        try:
            urlopen(req)
            count += 1
        except:
            pass
    return count

if __name__ == "__main__":
    if "--status" in sys.argv:
        # Show sync stats
        req = Request(f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll")
        req.add_header("Content-Type", "application/json")
        body = json.dumps({
            "filter": {"must": [{"key": "source", "match": {"value": "notion"}}]},
            "limit": 10
        }).encode()
        req.data = body
        req.method = "POST"
        try:
            resp = urlopen(req)
            data = json.loads(resp.read())
            print(f"📝 Notion pages in memory: {len(data.get('result', []))}")
        except:
            print("⚠️ No Notion data found")
        sys.exit(0)

    print("🔍 Syncing Notion...")
    token = load_token()
    pages = fetch_pages(token)
    print(f"  Found {len(pages)} pages/databases")
    
    if pages:
        stored = store_in_qdrant(pages)
        print(f"  ✅ Stored {stored} pages in Qdrant")
    else:
        print("  ⚠️ No pages found. Make sure your integration has access to pages.")
