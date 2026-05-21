#!/usr/bin/env python3
"""
RSS Aggregator — fetch RSS feeds and store in Qdrant memory.
Usage:
  python3 rss_aggregator.py          # Fetch all feeds
  python3 rss_aggregator.py --recent # Show last entries
  python3 rss_aggregator.py --feeds  # List configured feeds
"""
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import feedparser

QDRANT_URL = "http://localhost:6333"
COLLECTION = "pentagon_brain"

FEEDS = [
    ("Hacker News", "https://hnrss.org/frontpage?count=10"),
    ("ArXiv CS", "http://export.arxiv.org/rss/cs"),
    ("OpenClaw Releases", "https://github.com/openclaw/openclaw/releases.atom"),
    ("ComfyUI Releases", "https://github.com/comfyanonymous/ComfyUI/releases.atom"),
    ("Qdrant Blog", "https://qdrant.tech/blog/rss"),
]

DEDUP_FILE = os.path.expanduser("~/.openclaw/workspace/.rss_dedup.json")

def load_dedup():
    if os.path.exists(DEDUP_FILE):
        with open(DEDUP_FILE) as f:
            return json.load(f)
    return {}

def save_dedup(dedup):
    # Keep only last 500 entries to prevent file bloat
    if len(dedup) > 500:
        dedup = dict(list(dedup.items())[-500:])
    with open(DEDUP_FILE, "w") as f:
        json.dump(dedup, f)

def entry_hash(entry, feed_name):
    raw = f"{feed_name}:{entry.get('link', '')}:{entry.get('title', '')}"
    return hashlib.md5(raw.encode()).hexdigest()

def store_entry(entry, feed_name, eh):
    """Store a single entry in Qdrant."""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    pub_ts = time.mktime(published) if published else time.time()

    summary = entry.get("summary", "")[:500]
    title = entry.get("title", "Untitled")

    payload = {
        "source": "rss",
        "feed": feed_name.lower().replace(" ", "_"),
        "entry_hash": eh,
        "title": title,
        "url": entry.get("link", ""),
        "summary": summary,
        "published": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat(),
        "fetched_at": time.time(),
        "ttl_days": 7,
    }

    point_id = int(hashlib.md5(eh.encode()).hexdigest()[:15], 16) % (2**63)
    body = json.dumps({
        "points": [{"id": point_id, "vector": [0.0] * 384, "payload": payload}]
    }).encode()

    req = Request(f"{QDRANT_URL}/collections/{COLLECTION}/points", 
                  data=body, method="PUT")
    req.add_header("Content-Type", "application/json")
    try:
        urlopen(req)
        return True
    except Exception as e:
        print(f"    ⚠️ Qdrant error: {e}")
        return False

def fetch_feed(name, url):
    """Fetch and parse a single RSS feed."""
    print(f"  📡 {name}")
    try:
        feed = feedparser.parse(url)
        entries = feed.get("entries", [])
        print(f"     {len(entries)} entries")
        return entries
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return []

def show_recent():
    """Show last stored entries."""
    body = json.dumps({
        "filter": {"must": [{"key": "source", "match": {"value": "rss"}}]},
        "limit": 10,
        "with_payload": True,
    }).encode()
    req = Request(f"{QDRANT_URL}/collections/{COLLECTION}/points/scroll",
                  data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urlopen(req)
        data = json.loads(resp.read())
        points = data.get("result", [])
        if not points:
            print("⚠️ No RSS entries in memory")
            return
        print(f"\n📰 Recent RSS Entries ({len(points)}):")
        for p in points:
            pl = p.get("payload", {})
            print(f"  [{pl.get('feed','?')}] {pl.get('title','?')}")
            print(f"    {pl.get('url','')}")
    except Exception as e:
        print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    if "--recent" in sys.argv:
        show_recent()
        sys.exit(0)

    if "--feeds" in sys.argv:
        print("\n📡 Configured Feeds:")
        for name, url in FEEDS:
            print(f"  {name}: {url}")
        sys.exit(0)

    print("🔍 RSS Aggregator — $(date)")
    dedup = load_dedup()
    total_new = 0

    for name, url in FEEDS:
        entries = fetch_feed(name, url)
        new_count = 0
        for entry in entries:
            eh = entry_hash(entry, name)
            if eh in dedup:
                continue
            if store_entry(entry, name, eh):
                dedup[eh] = time.time()
                new_count += 1
        print(f"     {new_count} new entries stored")
        total_new += new_count

    save_dedup(dedup)
    print(f"\n✅ Done: {total_new} new entries across {len(FEEDS)} feeds")

    if total_new > 0:
        print(f"   Run with --recent to see them")
