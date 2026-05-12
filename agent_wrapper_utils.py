#!/usr/bin/env python3
"""
Agent Wrapper Utils - 裁判集成层

Phase 1: 收集 usage，报告给裁判
Phase 2/3: 接收裁判触发信号

关键设计：
- 裁判是唯一裁判，其他模块不能自主 action
- Agent 上报 usage 给裁判
- 裁判接收后决定是否触发 action
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

# 裁判接口 (裁判触发 action)
class SentinelGovernor:
    """裁判接口 - 其他模块必须通过裁判触发 action"""
    
    # 裁判唯一可以调用的函数 (需要实际实现)
    def compress_context(self, agent_id: str, usage: float) -> bool:
        """压缩上下文 - 只有裁判可以调用"""
        print(f"[SENTER] COMPRESS called (裁判调用): agent={agent_id}, usage={usage:.2%}")
        # TODO: 实际压缩逻辑
        return True
    
    def force_trim(self, agent_id: str, usage: float) -> bool:
        """强制 trim - 只有裁判可以调用"""
        print(f"[SENTER] FORCED_TRIM called (裁判调用): agent={agent_id}, usage={usage:.2%}")
        # TODO: 实际 trim 逻辑
        return True
    
    def abort_generation(self, agent_id: str, usage: float) -> bool:
        """中断生成 - 只有裁判可以调用"""
        print(f"[SENTER] ABORT called (裁判调用): agent={agent_id}, usage={usage:.2%}")
        # TODO: 实际 abort 逻辑
        return True

governor = SentinelGovernor()

# ========== Agent Usage 报告 (Phase 1: 只报告) ==========
def report_usage(agent_id: str, usage: float, context_tokens: int, max_tokens: int):
    """Agent 上报 usage 给裁判 (Phase 1)"""
    # 计算 usage
    usage = min(max(context_tokens / max_tokens, 0.0), 1.0)
    
    # 报告给裁判 (Phase 1: 只记录，不 action)
    # 真实部署：这里需要调用裁判的 actual implementation
    # 临时实现：直接打印 + 写入日志
    print(f"[AGENT] reporting usage to governor: agent={agent_id}, usage={usage:.2%}")
    
    # 写入日志
    log_file = Path.home() / ".openclaw" / "agent_usage.jsonl"
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'agent': agent_id,
        'usage': usage,
        'context_tokens': context_tokens,
        'max_tokens': max_tokens
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(event) + '\n')

# ========== Agent Budget 管理 (Phase 1/2/3) ==========
AGENT_BUDGETS = {
    'main': 0.40,
    'intel': 0.25,
    'ops': 0.15,
    'comms': 0.10,
    'sentinel': 0.10
}

def get_budget(agent_id: str) -> float:
    """获取 agent budget"""
    return AGENT_BUDGETS.get(agent_id, 0.10)

def check_budget_exceeded(agent_id: str, usage: float) -> bool:
    """检查是否超出 budget"""
    budget = get_budget(agent_id)
    return usage > budget

# ========== Cooldown 管理 (Phase 2/3) ==========
LAST_ACTION_TIME = {}  # agent_id -> timestamp
COOLDOWN_SECONDS = 5

def check_cooldown(agent_id: str) -> bool:
    """检查 cooldown - 裁判可以触发 action 的前提"""
    now = datetime.utcnow()
    last_time = LAST_ACTION_TIME.get(agent_id, now.timestamp())
    elapsed = (now - last_time).total_seconds()
    
    if elapsed > COOLDOWN_SECONDS:
        LAST_ACTION_TIME[agent_id] = now.timestamp()
        return True
    return False

def get_last_action_time(agent_id: str) -> float:
    """获取最后 action 时间"""
    return LAST_ACTION_TIME.get(agent_id, 0.0)

# ========== 裁判触发接口 (Phase 2/3) ==========
def trigger_compression(agent_id: str, usage: float) -> bool:
    """裁判触发 compression (Phase 2/3)"""
    if check_cooldown(agent_id):
        # 调用裁判实际压缩逻辑
        return governor.compress_context(agent_id, usage)
    return False

def trigger_trim(agent_id: str, usage: float) -> bool:
    """裁判触发 trim (Phase 3)"""
    if check_cooldown(agent_id):
        return governor.force_trim(agent_id, usage)
    return False

def trigger_abort(agent_id: str, usage: float) -> bool:
    """裁判触发 abort (Phase 3)"""
    if check_cooldown(agent_id):
        return governor.abort_generation(agent_id, usage)
    return False

# ========== 主入口 (测试) ==========
if __name__ == '__main__':
    print("Agent Wrapper Utils loaded - Phase 1: Usage Reporting")
    print(f"Agent Budgets: {AGENT_BUDGETS}")
    print(f"Cooldown: {COOLDOWN_SECONDS}s")
    
    # 测试 usage 报告
    report_usage('intel', 0.72, 36000, 50000)
    print("✓ Usage reporting working")
