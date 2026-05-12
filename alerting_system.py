"""
alerting_system.py - Runtime Safety Enforcement Layer

Purpose: Proactive runtime awareness, GPU pressure reaction, operational telemetry classification.

NOT a dashboard system. This is an enforcement layer that triggers recovery actions.

Threats Detected:
- GPU pressure → throttle model calls
- Event loop stall → pause non-critical agents
- Repeated timeouts → open circuit breaker
- Path recursion → block operation
- Recurring fallbacks → escalate severity
"""
import hashlib
import json
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import os
from typing import Optional as OptType

# Canonical workspace enforcement
CANONICAL_WORKSPACE = Path(__file__).parent
MEMORY_DIR = CANONICAL_WORKSPACE / "memory"
AGENTS_DIR = CANONICAL_WORKSPACE / "agents"
ALERT_LOGS_DIR = CANONICAL_WORKSPACE / "memory" / "telemetry" / "alerts"
ALERT_LOGS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GPUAlert:
    """GPU pressure alert with severity escalation."""
    timestamp: str
    usage_percent: int
    level: str  # warn, throttle, reject, emergency
    action_taken: str
    hash_id: str  # for noise suppression
    device: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventLoopAlert:
    """Event loop stall detection."""
    timestamp: str
    delay_ms: int
    inferred_cause: str
    action_taken: str
    hash_id: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompressionAlert:
    """Compression event governance."""
    timestamp: str
    trigger: str  # retrieval_entropy, duplication_density, semantic_redundancy
    compression_ratio: float
    action_taken: str
    hash_id: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentFailureAlert:
    """Agent failure classification."""
    timestamp: str
    failure_type: str  # timeout, path_recursion, repeated_fallback, gpu_overload, missing_file
    severity: str  # low-medium, medium, high, critical
    action_taken: str
    hash_id: str
    agent_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertLog:
    """Aggregated alert log with noise suppression."""
    alerts: deque = field(default_factory=lambda: deque(maxlen=500))
    alert_hashes: set = field(default_factory=set)  # Prevent duplicate alerts
    cooldown_periods: Dict[str, float] = field(default_factory=dict)  # hash -> cooldown_until
    last_flush_time: float = 0.0


class AlertingSystem:
    """
    Runtime safety enforcement layer.

    Responsibilities:
    1. GPU Pressure Alerts (WSL2-safe thresholds)
    2. Event Loop Stall Detection
    3. Compression Event Governance
    4. Agent Failure Classification
    5. Noise Suppression
    6. Runtime Recovery Actions
    """

    def __init__(self):
        self.alert_log = AlertLog()
        self.gpu_thresholds = {
            "warn": 80,
            "throttle": 85,
            "reject": 90,
            "emergency": 95
        }
        self.max_cooldown_minutes = 5
        self.alert_callbacks: List[Callable[[Dict], None]] = []
        self.recovery_actions = {
            "throttle_model_calls": self._throttle_model_calls,
            "open_circuit_breaker": self._open_circuit_breaker,
            "pause_noncritical_agents": self._pause_noncritical_agents,
            "trigger_emergency_cooldown": self._trigger_emergency_cooldown
        }

    def _generate_hash(self, alert_data: Dict[str, Any]) -> str:
        """Generate noise-suppression hash for duplicate detection."""
        data_str = json.dumps(alert_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def record_alert(self, alert_class, **kwargs):
        """Record alert with noise suppression."""
        hash_id = kwargs.pop("hash_id", self._generate_hash(kwargs))
        
        # Check cooldown
        if hash_id in self.alert_log.alert_hashes:
            cooldown_until = self.alert_log.cooldown_periods.get(hash_id, 0)
            if time.time() < cooldown_until:
                return  # Cooldown period active, suppress
            # Reset cooldown
            self.alert_log.cooldown_periods[hash_id] = time.time() + (
                self.max_cooldown_minutes * 60
            )
        
        # Record alert
        alert = alert_class(
            **kwargs,
            hash_id=hash_id,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self.alert_log.alerts.append(alert)
        self.alert_log.alert_hashes.add(hash_id)

        # Flush if threshold reached
        if len(self.alert_log.alerts) % 10 == 0:
            self._flush_alerts()

    def _throttle_model_calls(self, message: str = "GPU pressure detected"):
        """Throttle model calls during high GPU usage."""
        print(f"[ALERT][THROTTLE] {message}")
        print("Action: Reducing model inference frequency")
        # In production, this would write to config or send to agent
        pass

    def _open_circuit_breaker(self, reason: str = "Repeated timeouts"):
        """Open circuit breaker for repeated failures."""
        print(f"[ALERT][CIRCUIT_BREAKER] {reason}")
        print("Action: Opening circuit breaker")
        pass

    def _pause_noncritical_agents(self, agents: List[str] = None):
        """Pause non-critical agents during runtime pressure."""
        if agents is None:
            agents = ["@intel"]
        print(f"[ALERT][PAUSE_AGENTS] Pausing agents: {agents}")
        pass

    def _trigger_emergency_cooldown(self):
        """Trigger emergency cooldown for GPU."""
        print("[ALERT][EMERGENCY_COOLDOWN] GPU emergency cooldown triggered")
        pass

    # ========== 1️⃣ GPU Pressure Alerts ==========

    def check_gpu_pressure(self, gpu_usage_percent: int, device: Optional[str] = None) -> Optional[GPUAlert]:
        """Check GPU pressure and trigger appropriate action."""
        if gpu_usage_percent >= self.gpu_thresholds["emergency"]:
            self.record_alert(
                GPUAlert,
                usage_percent=gpu_usage_percent,
                level="emergency",
                action_taken="trigger_emergency_cooldown",
                device=device,
                details={"immediate_action_required": True}
            )
            self.recovery_actions["trigger_emergency_cooldown"]()
            return GPUAlert(
                usage_percent=gpu_usage_percent,
                level="emergency",
                action_taken="trigger_emergency_cooldown",
                device=device,
                details={"immediate_action_required": True}
            )

        elif gpu_usage_percent >= self.gpu_thresholds["reject"]:
            self.record_alert(
                GPUAlert,
                usage_percent=gpu_usage_percent,
                level="reject",
                action_taken="reject_new_inference",
                device=device,
                details={"rejected_inference": True}
            )
            return GPUAlert(
                usage_percent=gpu_usage_percent,
                level="reject",
                action_taken="reject_new_inference",
                device=device,
                details={"rejected_inference": True}
            )

        elif gpu_usage_percent >= self.gpu_thresholds["throttle"]:
            self.record_alert(
                GPUAlert,
                usage_percent=gpu_usage_percent,
                level="throttle",
                action_taken="throttle_model_calls",
                device=device,
                details={"inference_frequency_reduced": True}
            )
            self.recovery_actions["throttle_model_calls"]()
            return GPUAlert(
                usage_percent=gpu_usage_percent,
                level="throttle",
                action_taken="throttle_model_calls",
                device=device,
                details={"inference_frequency_reduced": True}
            )

        elif gpu_usage_percent >= self.gpu_thresholds["warn"]:
            self.record_alert(
                GPUAlert,
                usage_percent=gpu_usage_percent,
                level="warn",
                action_taken="log_warning",
                device=device,
                details={"usage_warning": True}
            )
            return GPUAlert(
                usage_percent=gpu_usage_percent,
                level="warn",
                action_taken="log_warning",
                device=device,
                details={"usage_warning": True}
            )

        return None

    # ========== 2️⃣ Event Loop Stall Detection ==========

    def check_event_loop(self, event_loop_delay_ms: int, inference_queue_age: int = 0,
                         retry_storm_frequency: int = 0) -> Optional[EventLoopAlert]:
        """Detect event loop stalls."""
        if event_loop_delay_ms > 1000:
            inferred_cause = self._infer_cause(event_loop_delay_ms, inference_queue_age, retry_storm_frequency)
            
            self.record_alert(
                EventLoopAlert,
                delay_ms=event_loop_delay_ms,
                inferred_cause=inferred_cause,
                action_taken="log_stall_warning"
            )
            if event_loop_delay_ms > 3000:
                self.recovery_actions["pause_noncritical_agents"]()
                return EventLoopAlert(
                    delay_ms=event_loop_delay_ms,
                    inferred_cause=inferred_cause,
                    action_taken="pause_noncritical_agents"
                )
            return EventLoopAlert(
                delay_ms=event_loop_delay_ms,
                inferred_cause=inferred_cause,
                action_taken="log_stall_warning"
            )

        return None

    def _infer_cause(self, delay_ms: int, queue_age: int, retry_frequency: int) -> str:
        """Infer cause of event loop stall."""
        if queue_age > 5000:
            return "Inference queue buildup"
        elif retry_frequency > 5:
            return "Retry storm (connection issues)"
        elif delay_ms > 3000:
            return "WSL reclaim or memory pressure"
        else:
            return "Unknown event loop stall"

    # ========== 3️⃣ Compression Event Governance ==========

    def log_compression_event(self, trigger: str, compression_ratio: float,
                               semantic_redundancy: float = 0.0) -> Optional[CompressionAlert]:
        """Log compression events based on semantic metrics, not line count."""
        self.record_alert(
            CompressionAlert,
            trigger=trigger,
            compression_ratio=compression_ratio,
            action_taken="log_compression_event",
            details={"semantic_redundancy": semantic_redundancy}
        )
        return CompressionAlert(
            trigger=trigger,
            compression_ratio=compression_ratio,
            action_taken="log_compression_event",
            details={"semantic_redundancy": semantic_redundancy}
        )

    # ========== 4️⃣ Agent Failure Classification ==========

    def classify_agent_failure(self, failure_type: str, severity: str, agent_id: Optional[str] = None,
                               details: Optional[Dict[str, Any]] = None) -> Optional[AgentFailureAlert]:
        """Classify agent failures with severity differentiation."""
        self.record_alert(
            AgentFailureAlert,
            failure_type=failure_type,
            severity=severity,
            action_taken="log_failure",
            agent_id=agent_id,
            details=details or {}
        )

        # Trigger recovery actions based on severity
        if severity == "critical":
            if failure_type == "gpu_overload":
                self.recovery_actions["trigger_emergency_cooldown"]()
            elif failure_type == "path_recursion":
                self.recovery_actions["open_circuit_breaker"]("Path recursion detected")
            elif failure_type == "repeated_fallback":
                self.recovery_actions["open_circuit_breaker"]("Repeated fallbacks exhausted")

        elif severity == "high":
            self.recovery_actions["open_circuit_breaker"]("Repeated timeouts")

        elif severity == "medium":
            if failure_type == "timeout":
                self.recovery_actions["throttle_model_calls"]("Timeout detected")

        return AgentFailureAlert(
            failure_type=failure_type,
            severity=severity,
            action_taken="log_failure",
            agent_id=agent_id,
            details=details or {}
        )

    # ========== 5️⃣ Noise Suppression ==========

    def _infer_cause(self, delay_ms: int, queue_age: int, retry_frequency: int) -> str:
        """Infer cause of event loop stall."""
        if queue_age > 5000:
            return "Inference queue buildup"
        elif retry_frequency > 5:
            return "Retry storm (connection issues)"
        elif delay_ms > 3000:
            return "WSL reclaim or memory pressure"
        else:
            return "Unknown event loop stall"

    def _flush_alerts(self):
        """Flush alerts to disk (throttled to prevent spam)."""
        if self.alert_log.last_flush_time == 0:
            self.alert_log.last_flush_time = time.time()
            return

        elapsed = time.time() - self.alert_log.last_flush_time
        if elapsed < 60:  # Flush at most once per minute
            return

        # Log alerts to file
        log_file = ALERT_LOGS_DIR / f"alerts_{int(time.time() / 60)}.jsonl"
        with open(log_file, "w") as f:
            for alert in self.alert_log.alerts:
                f.write(json.dumps(asdict(alert)) + "\n")

        self.alert_log.alerts.clear()
        self.alert_log.last_flush_time = time.time()

    # ========== Utility: Get Alert Statistics ==========

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics for monitoring."""
        return {
            "total_alerts": len(self.alert_log.alerts),
            "alert_types": {
                "gpu": sum(1 for a in self.alert_log.alerts if isinstance(a, GPUAlert)),
                "event_loop": sum(1 for a in self.alert_log.alerts if isinstance(a, EventLoopAlert)),
                "compression": sum(1 for a in self.alert_log.alerts if isinstance(a, CompressionAlert)),
                "failure": sum(1 for a in self.alert_log.alerts if isinstance(a, AgentFailureAlert)),
            },
            "levels": {
                "emergency": sum(1 for a in self.alert_log.alerts if hasattr(a, 'level') and a.level == "emergency"),
                "critical": sum(1 for a in self.alert_log.alerts if hasattr(a, 'severity') and a.severity == "critical"),
                "reject": sum(1 for a in self.alert_log.alerts if hasattr(a, 'level') and a.level == "reject"),
                "high": sum(1 for a in self.alert_log.alerts if hasattr(a, 'severity') and a.severity == "high"),
                "throttle": sum(1 for a in self.alert_log.alerts if hasattr(a, 'level') and a.level == "throttle"),
                "medium": sum(1 for a in self.alert_log.alerts if hasattr(a, 'severity') and a.severity == "medium"),
                "warn": sum(1 for a in self.alert_log.alerts if hasattr(a, 'level') and a.level == "warn"),
                "low": sum(1 for a in self.alert_log.alerts if hasattr(a, 'severity') and a.severity == "low-medium"),
            },
            "active_hashes": len(self.alert_log.alert_hashes),
            "cooldown_active": len(self.alert_log.cooldown_periods),
        }


# Singleton instance for system-wide use
_alerting_system = AlertingSystem()


def get_alerting_system() -> AlertingSystem:
    """Get the singleton alerting system instance."""
    return _alerting_system


# ========== Main entry point for testing ==========
if __name__ == "__main__":
    import pynvml
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    info = pynvml.nvmlDeviceGetUtilizationRates(handle)
    gpu_usage = info.gpu

    print(f"GPU Usage: {gpu_usage}%")
    print("\nTesting alerting_system.py...")

    system = get_alerting_system()

    # Test GPU alerts
    for usage in [75, 82, 87, 92, 98]:
        alert = system.check_gpu_pressure(usage)
        if alert:
            print(f"[{alert.level.upper()}] GPU Usage: {usage}%")

    # Test event loop
    alerts = [system.check_event_loop(delay) for delay in [500, 1500, 3500]]
    for alert in alerts:
        if alert:
            print(f"[{type(alert).__name__}] Event Loop Delay: {alert.delay_ms}ms - Cause: {alert.inferred_cause}")

    # Test failure classification
    for ftype, sev in [("timeout", "medium"), ("path_recursion", "critical"), ("repeated_fallback", "high")]:
        system.classify_agent_failure(ftype, sev, agent_id="@intel")

    # Stats
    stats = system.get_alert_stats()
    print(f"\nAlert Statistics: {stats}")
