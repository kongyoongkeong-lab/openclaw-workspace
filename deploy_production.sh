#!/bin/bash
# Production Deployment Script for Memory System v1
# Author: Pentagon Orchestrator @main
# Date: 2026-05-08

set -e

echo "🚀 Production Deployment - Memory System v1"
echo "=============================================="

# Create production memory directories
mkdir -p ~/openclaw-stack/production/memory
mkdir -p ~/openclaw-stack/production/logs

# Copy memory modules to production
cp memory_v1.py ~/openclaw-stack/production/memory/
cp compressor_ltm.py ~/openclaw-stack/production/memory/
cp sentinel_memory.py ~/openclaw-stack/production/memory/
cp memory_router.py ~/openclaw-stack/production/memory/
cp search_protocol.py ~/openclaw-stack/production/memory/
cp search_integration.py ~/openclaw-stack/production/memory/

# Create production memory files
touch ~/openclaw-stack/production/memory/episodic.jsonl
touch ~/openclaw-stack/production/memory/semantic.jsonl
touch ~/openclaw-stack/production/memory/agents/*.jsonl

echo "✅ Memory system deployed to production"
echo "✅ Production directories created"
echo "✅ All memory modules in place"

# Set permissions
chmod 644 ~/openclaw-stack/production/memory/*

echo "🎉 Production deployment complete!"