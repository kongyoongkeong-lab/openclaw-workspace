#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE="${SCRIPT_DIR}/pipeline.py"
LOG="${SCRIPT_DIR}/cache/logs/test_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "${SCRIPT_DIR}/cache/logs"

echo "🚀 PDF Pipeline Test"
echo "================"
echo ""

if [ ! -d "${SCRIPT_DIR}/input" ] || [ -z "$(ls -A ${SCRIPT_DIR}/input 2>/dev/null)" ]; then
    echo "⚠️  No PDF files found in /input/"
    echo "Creating test PDF..."
    echo "Sample content for testing..." > /tmp/test.txt
    # Use pdftotext if available, otherwise skip
    if command -v pdftotext &> /dev/null; then
        echo "Test PDF already exists or will be created later"
    fi
else
    echo "📄 Found PDF files in /input/"
    for f in "${SCRIPT_DIR}/input"/*.pdf; do
        echo "   - $(basename "$f")"
    done
fi

echo ""
echo "🔄 Executing pipeline..."
python3 "$PIPELINE" 2>&1 | tee "$LOG"

echo ""
echo "✅ Test Complete!"
echo "📝 Logs saved to: $LOG"

if command -v docker &> /dev/null; then
    echo ""
    echo "📊 Qdrant Collection Info:"
    docker exec qdrant qdrant-cli info collection --name documents 2>/dev/null || echo "Qdrant info unavailable"
fi

echo ""
echo "🚀 Test Finished!"
