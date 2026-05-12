#!/bin/bash
# Pentagon Queue Status Check

COMFY_STATUS="http://localhost:8188/queue"
COMFY_HISTORY="http://localhost:8188/history"

echo "=== ComfyUI Queue Status ==="
curl -s "$COMFY_STATUS" | jq '.'

echo ""
echo "=== Recent Generation History ==="
curl -s "$COMFY_HISTORY" | jq '.'
