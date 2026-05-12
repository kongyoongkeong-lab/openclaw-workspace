#!/bin/bash
# Pentagon ComfyUI API Queue Script

COMFY_API="http://localhost:8188/prompt"
WORKFLOW_DIR="$HOME/.openclaw/workspace/pentagon/comfyui/workflows"

# Usage: ./queue_generation.sh [workflow_path] [prompt]
# Default: use first_sdxl_workflow.json

WORKFLOW="${1:-$WORKFLOW_DIR/first_sdxl_workflow.json}"

if [ ! -f "$WORKFLOW" ]; then
    echo "❌ Workflow not found: $WORKFLOW"
    exit 1
fi

echo "🚀 Queuing generation via API..."
curl -X POST "$COMFY_API" \
    -H "Content-Type: application/json" \
    -d @"$WORKFLOW" | jq '.'

echo "✅ Generation queued. Check output in: $HOME/pentagon/comfyui/output/"
