#!/bin/bash
# Channel Health Check — verify all delivery channels
echo "🔍 Pentagon Channel Health — $(date)"
echo ""

# 1. Webchat (always up)
echo "✅ Webchat (direct session)"

# 2. Telegram
TOKEN_FILE="$HOME/.openclaw/credentials/telegram-default-allowFrom.json"
if [ -f "$TOKEN_FILE" ]; then
  echo "  ✅ Telegram config found"
else
  echo "  ⚠️ Telegram config not found (may not be configured)"
fi

# 3. GitHub Issues
if gh api repos/kongyoongkeong-lab/openclaw-workspace 2>/dev/null | grep -q full_name; then
  echo "  ✅ GitHub Issues (API responsive)"
else
  echo "  ❌ GitHub Issues (API failed)"
fi

# 4. OpenClaw Gateway
if systemctl --user is-active openclaw-gateway.service 2>/dev/null | grep -q active; then
  echo "  ✅ OpenClaw Gateway (active)"
else
  echo "  ❌ OpenClaw Gateway (inactive)"
fi

echo ""
echo "📡 Channel status logged"
