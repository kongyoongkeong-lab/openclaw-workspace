#!/bin/bash

# 🚀 Pentagon Stack Sync Script
# Purpose: GitOps synchronization of control plane only
# Security: Explicitly excludes runtime state via .gitignore
# Provenance: Semantic commits with timestamps

set -euo pipefail

echo "🚀 Pentagon Stack Sync Initiated..."

TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Add only control-plane files (runtime state excluded via .gitignore)
git add .

# Commit with provenance-aware message
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit."
else
    git commit -m "sync(runtime): Pentagon Stack snapshot

- branch: $BRANCH
- timestamp: $TIMESTAMP
- scope: control-plane only
- state: excluded (runtime isolated)"
    
    # Push to remote (if available)
    if git remote -q show origin >/dev/null 2>&1; then
        git push origin main
    fi
    
    echo "✅ Sync complete @ $TIMESTAMP"
else
    echo "✅ No changes detected. Skipping sync."
fi
