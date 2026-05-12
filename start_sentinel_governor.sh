#!/bin/bash
# Sentinel Context Governor - Start Script
# Phase 1: Passive Monitoring (Monitor only, no action)

echo "=============================================="
echo "  Sentinel Context Governor - Starting"
echo "=============================================="
echo ""

# 配置路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/home/jason2ykk/.openclaw"
CONTEXT_MONITOR="$LOG_DIR/context_monitor.jsonl"
AGENT_USAGE="$LOG_DIR/agent_usage.jsonl"

# 日志
LOG_FILE="$LOG_DIR/sentinel_governor.log"

# 启动裁判 Python 脚本
echo "[SENTINEL] Phase 1: Passive Monitoring Mode"
echo "[SENTINEL] Agent Budgets:"
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from agent_wrapper_utils import AGENT_BUDGETS
for agent, budget in AGENT_BUDGETS.items():
    print(f'  {agent}: {budget:.2%}')
"

echo ""
echo "[SENTINEL] Cooldown: 5 seconds"
echo "[SENTINEL] Actions allowed: COMPRESS at 85%, TRIM at 90%, ABORT at 95%"
echo "[SENTINEL] Current phase: Phase 1 (Passive Monitoring)"
echo ""

echo "[SENTINEL] 日志输出位置:"
echo "  - 决策日志：$CONTEXT_MONITOR"
echo "  - Agent usage: $AGENT_USAGE"
echo "  - 运行日志：$LOG_FILE"

# 启动 Python 裁判监控
echo ""
echo "[SENTINEL] 启动监控循环..."
python3 "$SCRIPT_DIR/sentinel_context.py" &
GOVERNOR_PID=$!

echo "[SENTINEL] Governor PID: $GOVERNOR_PID"
echo "[SENTINEL] 等待 Governor 完成..."

# 等待进程 (Phase 1 应该是无限循环，等待 Ctrl+C)
wait $GOVERNOR_PID

# 清理
echo ""
echo "[SENTINEL] Governor 已停止"
echo "[SENTINEL] 检查日志:"
echo "  - $(wc -l < $CONTEXT_MONITOR) 条决策记录"
echo "  - $(wc -l < $AGENT_USAGE) 条 usage 报告"

# 显示最后几条日志
echo ""
echo "[SENTINEL] 最近 5 条决策:"
tail -5 "$CONTEXT_MONITOR"

echo ""
echo "=============================================="
echo "  Sentinel Context Governor - Ready"
echo "=============================================="
echo ""
echo "To stop: Ctrl+C (send SIGINT)"
echo "To check logs: cat $CONTEXT_MONITOR"
echo "To view usage: cat $AGENT_USAGE"

