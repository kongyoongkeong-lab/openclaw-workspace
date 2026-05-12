#!/usr/bin/env python3
"""
Sentinel Context Governor - Passive Monitoring Mode
Phase 1: 只监控 + 打日志，不干预系统

关键设计：
- 唯一裁判 (唯一触发权限)
- Cooldown 防止无限循环
- Agent budget (intel:25%, ops:15%, comms:10%, sentinel:10%, main:40%)
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ========== 阈值配置 ==========
THRESHOLDS = {
    'WARNING': 0.80,
    'AUTO_COMPRESS': 0.85,
    'FORCED_TRIM': 0.90,
    'EMERGENCY_ABORT': 0.95
}

# ========== Agent Budget (总 context 分配) ==========
AGENT_BUDGETS = {
    'main': 0.40,
    'intel': 0.25,
    'ops': 0.15,
    'comms': 0.10,
    'sentinel': 0.10
}

# ========== 全局状态 (裁判唯一可访问) ==========
class GovernorState:
    """裁判全局状态 - 其他模块无法直接修改"""
    def __init__(self):
        self.last_action_time = {}  # agent_id -> last action time
        self.current_usage = {}     # agent_id -> current usage
        self.action_history = []    # 决策历史
        self.emergency_count = 0
        
    def can_act(self, agent_id: str, action: str) -> bool:
        """裁判决策：是否可以执行 action"""
        cooldown_seconds = 5  # 关键：防止无限压缩循环
        now = datetime.utcnow()
        last_time = self.last_action_time.get(agent_id, now.timestamp())
        elapsed = (now - last_time).total_seconds()
        
        if elapsed > cooldown_seconds:
            self.last_action_time[agent_id] = now.timestamp()
            return True
        return False
    
    def record_decision(self, agent_id: str, usage: float, action: str, 
                       reason: str):
        """裁判记录决策"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'agent': agent_id,
            'usage': usage,
            'action': action,
            'reason': reason,
            'mode': 'phase1_passive' if action != 'NONE' else 'phase1_monitor_only',
            'cooldown_elapsed': True  # Phase 1: 无条件允许
        }
        self.action_history.append(event)
        # 日志文件：gateway 可访问
        log_path = Path.home() / ".openclaw" / "context_monitor.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')

# 裁判实例
governor_state = GovernorState()

def check_action_allowed(agent_id: str, action: str) -> bool:
    """裁判 gate: 是否允许执行 action"""
    # 只有 governor 才能调用此函数
    return governor_state.can_act(agent_id, action)

def log_decision(agent_id: str, usage: float, action: str, reason: str):
    """裁判记录决策"""
    governor_state.record_decision(agent_id, usage, action, reason)

# ========== Usage 计算 (Phase 1: 被动监控) ==========
def calculate_usage(context_size: int, max_tokens: int) -> float:
    """裁判计算 usage = context_size / max_tokens"""
    usage = min(max(context_size / max_tokens, 0.0), 1.0)
    return usage

# ========== 日志输出 (Phase 1) ==========
def passive_monitor(agent_id: str, usage: float, timestamp: str = None):
    """裁判被动监控：只记录，不干预"""
    agent_usage = usage  # agent-level usage
    agent_budget = AGENT_BUDGETS.get(agent_id, 0.10)
    
    event = {
        'timestamp': timestamp or datetime.utcnow().isoformat(),
        'agent': agent_id,
        'usage': agent_usage,
        'agent_budget': agent_budget,
        'phase': '1_passive_monitor',
        'status': 'MONITORING'
    }
    
    print(f"[SENTINEL] Phase1 Monitoring: agent={agent_id}, usage={usage:.2%}, status=MONITORING")
    
    log_decision(agent_id, usage, 'NONE', 'Passive monitoring only - no action taken')

# ========== 主循环 (Phase 1) ==========
async def monitor_loop():
    """裁判主循环 - Phase 1: Passive Monitoring"""
    print(f"[SENTINEL] Governor 启动 - Phase1 Passive Monitoring")
    print(f"[SENTINEL] Agent Budgets: {AGENT_BUDGETS}")
    print(f"[SENTINEL] Cooldown: 5s, Emergency count: 0")
    
    # 模拟 agent usage 上报 (真实部署时需要从 agent 调用获取)
    # 真实部署：在 agent 执行后调用 agent_report_usage(agent_id, usage)
    
    while True:
        # 等待 agent usage 上报 (真实场景需要集成到 agent 调用链路)
        # 这里等待 2 秒模拟
        await asyncio.sleep(2)
        
        # Phase 1: 只记录，不干预
        # 这里应该从 agent 获取 usage，但 Phase 1 重点是验证系统
        # 暂时用静态值模拟
        usage_values = [
            ('intel', 0.72),
            ('ops', 0.68),
            ('comms', 0.55),
            ('sentinel', 0.45),
            ('main', 0.35)
        ]
        
        for agent_id, usage in usage_values:
            passive_monitor(agent_id, usage)
            print(f"  {agent_id}: usage={usage:.2%}, budget={AGENT_BUDGETS[agent_id]:.2%}")

# ========== 集成点 (待 Phase 2/3 启用) ==========
async def agent_report_usage(agent_id: str, usage: float) -> bool:
    """裁判接收 agent 上报的 usage (Phase 1 只记录)"""
    usage = min(max(usage, 0.0), 1.0)
    timestamp = datetime.utcnow().isoformat()
    passive_monitor(agent_id, usage, timestamp)
    return True

# ========== 主入口 ==========
if __name__ == '__main__':
    asyncio.run(monitor_loop())
