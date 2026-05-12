#!/usr/bin/env python3
"""
🧩 Self-Repair Orchestrator
Unified repair decision authority for the Pentagon runtime.
Aggregates all failure signals → assigns priorities → enforces single-action-per-cycle discipline.
"""

import time
import threading
import json
from enum import IntEnum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


class FailurePriority(IntEnum):
    """Failure severity levels with atomic ordering."""
    CRITICAL = 0    # Workspace corruption, GPU runaway
    HIGH = 1        # Timeout storm, GPU overheating
    MEDIUM = 2      # Memory pressure, compression drift
    LOW = 3         # Logging cleanup, minor anomalies


class ActionState(IntEnum):
    """Atomic state machine for repair actions."""
    COOLDOWN = 0    # Prevent concurrent repairs
    EXECUTING = 1   # Currently executing repair
    READY = 2       # Queue available for execution


@dataclass
class FailureSignal:
    """Raw failure signal from subsystems."""
    source: str           # GPU, memory, timeout, workspace, compression
    message: str          # Error/text signal
    timestamp: float      # When detected
    severity: FailurePriority
    context: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "source": self.source,
            "message": self.message,
            "timestamp": self.timestamp,
            "severity": self.severity.name,
            "context": self.context
        }


@dataclass
class RepairAction:
    """Atomic repair action with state machine."""
    name: str
    func: Callable
    cooldown_ms: int
    priority: FailurePriority
    
    state: ActionState = ActionState.COOLDOWN
    attempts: int = 0
    last_run: float = 0
    success_count: int = 0
    consecutive_failures: int = 0
    
    def execute(self, context):
        """Execute repair with atomic state transition."""
        if self.state != ActionState.READY:
            raise RuntimeError(f"Action {self.name} in state: {self.state.name}")
        
        self.state = ActionState.EXECUTING
        self.last_run = time.time()
        self.attempts += 1
        
        try:
            result = self.func(context)
            if result is not None and result.get("success", False):
                self.success_count += 1
                self.consecutive_failures = 0
                return {"success": True, "action": self.name, "result": result}
            else:
                self.consecutive_failures += 1
                return {"success": False, "action": self.name, "error": result or "Unknown failure"}
        except Exception as e:
            self.consecutive_failures += 1
            return {"success": False, "action": self.name, "error": str(e)}
    
    def can_execute(self):
        """Check if action is ready to run."""
        now = time.time()
        cooldown_sec = self.cooldown_ms / 1000
        return (now - self.last_run) >= cooldown_sec and self.state == ActionState.COOLDOWN
    
    def reset_cooldown(self):
        """Reset cooldown immediately (for high-priority override)."""
        self.state = ActionState.COOLDOWN
        self.attempts = 0
        self.success_count = 0
        self.consecutive_failures = 0


class RepairOrchestrator:
    """
    🧠 Central repair authority.
    
    Responsibilities:
    1. Aggregate signals from all subsystems
    2. Assign priority weights and detect conflicts
    3. Enforce single-action-per-cycle discipline
    4. Coordinate cooldown windows across repairs
    5. Log decision rationale for audit
    """
    
    def __init__(self, log_path="/home/jason2ykk/.openclaw/workspace/repair_logs.jsonl"):
        self.log_path = log_path
        self.actions: Dict[str, RepairAction] = {}
        self.signals: List[FailureSignal] = []
        self.last_decision_time: float = 0
        self.log_lock = threading.Lock()
        
        self._register_default_actions()
        self._log_decision("initialized", "System ready")
    
    def _register_default_actions(self):
        """Register repair actions with priorities and cooldowns."""
        
        def workspace_cleaner(context):
            # Clear corrupted workspace files
            import shutil
            workspace = context.get("workspace", "/app/workspace/")
            corrupted = context.get("corrupted_files", [])
            if corrupted:
                for f in corrupted:
                    try:
                        path = f"{workspace}{f}"
                        if path and __import__("os").path.exists(path):
                            __import__("os").remove(path)
                            return {"success": True, "cleared": f}
                    except Exception as e:
                        return {"success": True, "error": str(e)}
            return {"success": True, "action": "workspace_cleanup"}
        
        def gpu_throttle(context):
            # Set nvidia-smi -lgm or adjust power limit
            try:
                import subprocess
                subprocess.run(["nvidia-smi", "-pl", "80"], check=False)
                return {"success": True, "power_limit": 80}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        def circuit_breaker_open(context):
            # Disable problematic agent runtime hooks
            context["agent_runtime_disabled"] = True
            context["enabled_agents"] = context.get("active_agents", ["@intel", "@ops"])
            return {"success": True, "disabled": "circuit_breaker"}
        
        def compression_trigger(context):
            # Flush episodic memory or evict oldest chunks
            memory = context.get("memory_state", {})
            if memory.get("episodes", []):
                oldest = memory["episodes"].pop(0)
                return {"success": True, "evicted": oldest}
            return {"success": True, "action": "compression_cleanup"}
        
        def log_cleanup(context):
            # Rotate logs and prune old entries
            import os
            log_dir = context.get("log_dir", "/app/workspace/")
            for root, dirs, files in os.walk(log_dir):
                for f in files:
                    if f.endswith(".jsonl"):
                        full_path = os.path.join(root, f)
                        try:
                            with open(full_path) as file:
                                lines = file.readlines()
                                if len(lines) > 1000:
                                    keep = lines[-500:]
                                    with open(full_path, "w") as new_file:
                                        new_file.writelines(keep)
                            return {"success": True, "rotated": full_path}
                        except Exception as e:
                            return {"success": True, "error": str(e)}
            return {"success": True, "action": "log_cleanup"}
        
        self.actions["workspace_integrity"] = RepairAction(
            name="workspace_integrity",
            func=workspace_cleaner,
            cooldown_ms=30000,
            priority=FailurePriority.CRITICAL
        )
        
        self.actions["gpu_throttle"] = RepairAction(
            name="gpu_throttle",
            func=gpu_throttle,
            cooldown_ms=60000,
            priority=FailurePriority.CRITICAL
        )
        
        self.actions["circuit_breaker"] = RepairAction(
            name="circuit_breaker",
            func=circuit_breaker_open,
            cooldown_ms=120000,
            priority=FailurePriority.HIGH
        )
        
        self.actions["compression_trigger"] = RepairAction(
            name="compression_trigger",
            func=compression_trigger,
            cooldown_ms=45000,
            priority=FailurePriority.MEDIUM
        )
        
        self.actions["log_cleanup"] = RepairAction(
            name="log_cleanup",
            func=log_cleanup,
            cooldown_ms=300000,
            priority=FailurePriority.LOW
        )
    
    def add_signal(self, source: str, message: str, severity: FailurePriority, context: Dict = None):
        """Aggregate new failure signal."""
        signal = FailureSignal(
            source=source,
            message=message,
            timestamp=time.time(),
            severity=severity,
            context=context or {}
        )
        with self.log_lock:
            self.signals.append(signal)
        
        # Auto-recoverable signals → trigger action
        if severity in (FailurePriority.CRITICAL, FailurePriority.HIGH):
            self._evaluate_signals()
    
    def _evaluate_signals(self):
        """
        Decision engine: aggregate signals → select ONE action → execute.
        """
        now = time.time()
        
        # Filter recent signals (last 60 seconds)
        recent_signals = [
            s for s in self.signals 
            if (now - s.timestamp) < 60
        ]
        
        if not recent_signals:
            with self.log_lock:
                self.signals.clear()
            self._log_decision("no_signals", "No active signals")
            return
        
        # Sort by priority (ascending = most critical first)
        recent_signals.sort(key=lambda s: s.severity)
        
        # Group by source to avoid conflicts
        action_candidates = {}
        for signal in recent_signals:
            # Find matching repair action
            action_key = f"{signal.source}_repair"
            for key, action in self.actions.items():
                if key.startswith(signal.source.lower()):
                    if key not in action_candidates:
                        action_candidates[key] = {"action": action, "signal": signal}
                    break
        
        if not action_candidates:
            self._log_decision("no_actions", f"No repair actions for signals: {[s.source for s in recent_signals]}")
            return
        
        # SELECT HIGHEST PRIORITY ACTION ONLY (single-action-per-cycle discipline)
        # Detect conflicts: prefer CRITICAL over HIGH, etc.
        highest_priority_action = None
        highest_signal = None
        
        for candidate_signals in action_candidates.values():
            # Check if this action is ready (cooldown expired)
            candidate = candidate_signals["action"]
            if candidate.can_execute():
                # Override cooldown if higher priority than queued action
                queued_action = self._get_queued_action()
                if queued_action:
                    if candidate.priority < queued_action.priority:
                        # Higher priority - interrupt lower
                        candidate.reset_cooldown()
                        action_candidates.pop(queued_action.name)
                    elif candidate.priority > queued_action.priority:
                        continue  # Skip, already handling higher priority
        
        if action_candidates:
            # Pick highest priority ready action
            ready_actions = [c["action"] for c in action_candidates.values() if c["action"].can_execute()]
            highest_action = max(ready_actions, key=lambda a: a.priority)
            highest_signal = next(
                s for s in recent_signals 
                if s.source.lower() in highest_action.name.lower()
            )
            
            self._log_decision(
                "action_selected",
                f"Signal: {highest_signal.source} ({highest_signal.severity.name}) "
                f"→ Action: {highest_action.name} (Priority: {highest_action.priority.name})",
                context={"signal": highest_signal.to_dict(), "action": highest_action.name}
            )
            
            # Execute
            result = highest_action.execute(highest_signal.context)
            with self.log_lock:
                self._log_decision(
                    "action_executed",
                    f"Executed: {highest_action.name}",
                    context={"result": result, "signal": highest_signal.to_dict()}
                )
            
            return result
        
        else:
            # All actions in cooldown or higher priority conflict
            queued = self._get_queued_actions()
            self._log_decision(
                "actions_queued",
                f"All repair actions on cooldown. Queued: {queued}",
                context={"queued": queued}
            )
            return None
    
    def _get_queued_action(self):
        return next(
            (a for a in self.actions.values() 
             if not a.can_execute() and a.priority < FailurePriority.HIGH),
            None
        )
    
    def _get_queued_actions(self):
        return [
            a for a in self.actions.values()
            if not a.can_execute() and a.priority < FailurePriority.HIGH
        ]
    
    def _log_decision(self, decision_type: str, message: str, context: Dict = None):
        """Append decision audit log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision_type,
            "message": message,
            "context": context or {}
        }
        
        with self.log_lock:
            try:
                with open(self.log_path, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"[ORCHESTRATOR] Log write error: {e}")
    
    def get_health_summary(self) -> Dict:
        """Get current health snapshot."""
        now = time.time()
        
        active_signals = [s for s in self.signals if (now - s.timestamp) < 120]
        queued_actions = self._get_queued_actions()
        
        return {
            "active_signals_count": len(active_signals),
            "queued_actions_count": len(queued_actions),
            "signal_recent": [s.to_dict() for s in active_signals],
            "queued": [{"name": a.name, "cooldown": a.cooldown_ms} for a in queued_actions]
        }


# Singleton for runtime-wide usage
_orchestrator: Optional[RepairOrchestrator] = None


def get_orchestrator() -> RepairOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = RepairOrchestrator()
    return _orchestrator


def register_failure(source: str, message: str):
    """Register failure signal (simplified interface)."""
    severity_map = {
        "workspace": FailurePriority.CRITICAL,
        "gpu": FailurePriority.CRITICAL,
        "timeout": FailurePriority.HIGH,
        "compression": FailurePriority.MEDIUM,
        "logging": FailurePriority.LOW,
    }
    context = {
        "source": source,
        "message": message,
        "timestamp": time.time(),
    }
    orchestrator = get_orchestrator()
    orchestrator.add_signal(source, message, severity_map.get(source, FailurePriority.MEDIUM), context)


def get_health() -> Dict:
    """Get runtime health summary."""
    return get_orchestrator().get_health_summary()
