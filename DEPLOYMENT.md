# Pentagon Production Deployment

## 📦 Modules
- ✅ `memory_v1.py` - Storage layer (JSONL-based)
- ✅ `compressor_ltm.py` - Context compression module
- ✅ `test_compressor.py` - Test suite
- ✅ `sentinel_memory.py` - Memory learning system
- ✅ `memory_router.py` - Integration layer for agents
- ✅ `search_protocol.py` - Web search chain (DDG→Tavily→Google)
- ✅ `search_integration.py` - Agent integration layer
- ✅ `spg.py` - System Pressure Governor

## 🚀 Deployment Steps
```bash
# 1. Copy modules to Gateway node
scp *.py user@gateway:/app/workspace/

# 2. Gateway applies modules
gateway config.apply

# 3. Verify deployment
openclaw status
```

## 🔐 Secrets
- **Tavily API Key**: Set in environment (`TAVILY_API_KEY`)
- **Telegram Bot Token**: Inject via runtime, not hardcoded

## 📊 Metrics
- EPISODIC/SEMANTIC counters: Track memory growth
- PRESSURE SIGNAL: SPG zones (SAFE/EARLY/THROTTLE/CRITICAL/EMERGENCY)
- COMPRESSION: 50% ratio when lines > 3000

## ⚠️ Alerts
When `spg` zone reaches `CRITICAL` or `EMERGENCY`:
1. Halt non-critical operations
2. Trigger memory compression
3. Log alert to episodic memory

## 🔄 Updates
```bash
# Pull latest changes
git pull origin main

# Restart Gateway (if needed)
gateway config.apply
```
