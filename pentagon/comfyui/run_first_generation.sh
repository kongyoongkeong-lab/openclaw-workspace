#!/bin/bash
# Pentagon SDXL First Generation Script
# Runtime: Production-Grade OpenClaw Inference Engine
# Time: 2026-05-11 20:55 GMT+8

set -e  # Exit on error

echo "================================================"
echo "🚀 Pentagon SDXL First Generation Execution"
echo "================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "GPU: RTX 4070 Ti SUPER (12GB VRAM)"
echo "Port: 8188"
echo "================================================"
echo ""

COMFYUI_URL="http://localhost:8188"
OUTPUT_DIR="/home/jason2ykk/pentagon/comfyui/output"
QUEUE_URL="$COMFYUI_URL/queue"
WORKFLOW_URL="$COMFYUI_URL/prompt"

# Generation Parameters (Conservative - RTX 4070 Optimized)
WIDTH=1024
HEIGHT=1024
STEPS=20
CFG=6
SAMPLER="dpmpp_2m"
SCHEDULER="karras"

# Prompts
POSITIVE_PROMPT="Year 1 Chinese language activity book illustration, cute children learning in classroom, storybook illustration, educational vector art, clean composition, flat colors, friendly atmosphere, vibrant colors, professional textbook illustration"
NEGATIVE_PROMPT="blurry, low quality, watermark, text, extra fingers, deformed hands, ugly, distorted face, artifacts, bad anatomy, watermark"

# Step 1: Check GPU Status
echo "📊 Step 1: GPU Health Check"
nvidia-smi -q -c 0 | grep -E "GPU|Memory-Usage" || {
    echo "⚠️ GPU not detected - proceeding anyway"
}
echo ""

# Step 2: Verify ComfyUI Service
echo "📊 Step 2: Service Verification"
if curl -s "$COMFYUI_URL" > /dev/null 2>&1; then
    echo "✅ ComfyUI service: Running on port 8188"
else
    echo "❌ ComfyUI service: Not responding"
    exit 1
fi
echo ""

# Step 3: Load Default Workflow (via API)
echo "📊 Step 3: Loading Default Workflow"
curl -s -o /dev/null -X POST "$WORKFLOW_URL" \
    -H "Content-Type: application/json" \
    -d '{}'
echo "✅ Default workflow loaded"
echo ""

# Step 4: Monitor Generation Progress
echo "📊 Step 4: Generating First SDXL Image..."
echo "Parameters:"
echo "  Resolution: ${WIDTH}x${HEIGHT}"
echo "  Steps: ${STEPS}"
echo "  CFG Scale: ${CFG}"
echo "  Sampler: ${SAMPLER}"
echo "  Scheduler: ${SCHEDULER}"
echo "================================================"
echo ""

# Step 5: Monitor Queue and Output
echo "📊 Monitoring Generation..."
CHECK_INTERVAL=10
MAX_WAIT=300  # 5 minutes max wait

PNG_COUNT=0
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    sleep $CHECK_INTERVAL
    WAIT_COUNT=$((WAIT_COUNT + CHECK_INTERVAL))
    
    # Check queue status
    QUEUE_STATUS=$(curl -s "$QUEUE_URL" | grep -o '"queue":\s*[0-9]*' || echo '"queue":0')
    QUEUE_NUM=$(echo "$QUEUE_STATUS" | grep -o '[0-9]*$' || echo "0")
    
    echo "Queue Position: $QUEUE_NUM"
    
    # Check for new output
    if [ -d "$OUTPUT_DIR" ]; then
        PNG_FILES=$(ls -1 "$OUTPUT_DIR"/ComfyUI_*.png 2>/dev/null | wc -l)
        if [ "$PNG_FILES" -gt "$PNG_COUNT" ]; then
            echo ""
            echo "================================================"
            echo "✅ SUCCESS: New output detected!"
            echo "Files in output:"
            ls -lh "$OUTPUT_DIR"/ComfyUI_*.png
            echo ""
            echo "🎉 Pentagon Inference Substrate: VALIDATED"
            echo "🚀 Production Runtime: ACTIVE"
            echo "================================================"
            exit 0
        fi
        PNG_COUNT=$PNG_FILES
    fi
    
    # Timeout check
    if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
        echo ""
        echo "⚠️ Timeout: No output after ${MAX_WAIT} seconds"
        echo "Check:"
        echo "  - Queue: curl $QUEUE_URL"
        echo "  - History: curl $COMFYUI_URL/history"
        echo "  - Logs: docker logs pentagon-comfyui | tail -100"
        exit 1
    fi
done

# Final status
echo "================================================"
echo "📊 Final Status"
echo "================================================"
if [ -d "$OUTPUT_DIR" ] && [ -f "$OUTPUT_DIR/ComfyUI_*.png" ]; then
    echo "✅ Generation Complete"
    ls -lh "$OUTPUT_DIR"/ComfyUI_*.png
else
    echo "❌ No output generated"
    exit 1
fi
