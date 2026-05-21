#!/usr/bin/env python3
"""
Pentagon System - Signal Integration Layer
Wires GPU/timeout/workspace/memory signals to orchestrator failure registration.
"""

import re
import os
import sys
from pathlib import Path
from typing import Callable, Optional, List
import threading
import time
from datetime import datetime

# Base imports
from integration import failure_registration
from integration import config_reader
from integration import gpu_timeout_guard
from integration import workspace_guard
from integration import memory_guard


class SignalHandler:
    """Central signal handler for orchestrator failure registration."""
    
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance
        self.handlers: List[Callable] = []
        self.lock = threading.Lock()
        self.signal_sources = {
            'GPU_RUNAWAY': None,
            'TIMEOUT_STORM': None,
            'PATH_CORRUPTION': None,
            'MEMORY_PRESSURE': None
        }
        self.callbacks = {
            'GPU_RUNAWAY': [],
            'TIMEOUT_STORM': [],
            'PATH_CORRUPTION': [],
            'MEMORY_PRESSURE': []
        }
    
    def register_gpu_guard(self, guard_instance):
        """Wire GPU timeout guard to failure registration."""
        print(f"[SIGNAL] Registering GPU timeout guard handler...")
        
        def handler(message, level=1):
            with self.lock:
                print(f"[SIGNAL] GPU_TIMEOUT detected: {message}")
                # Check for VRAM runaway patterns
                if 'VRAM_RUNAWAY' in message or 'memory limit' in message.lower():
                    if self.orchestrator.config.get('gpu_guard.enabled', False):
                        failure_registration.register_failure(
                            event_id='GPU_RUNAWAY',
                            severity='CRITICAL',
                            message=message,
                            level=level
                        )
                        self.orchestrator.metrics.increment('gpu.timeout', 1)
                        self.orchestrator.logger.warning(
                            f"GPU timeout guard triggered: {message}"
                        )
                        for callback in self.callbacks['GPU_RUNAWAY']:
                            callback(message, level)
                return False
        
        self.signal_sources['GPU_RUNAWAY'] = handler
        self.handlers.append(handler)
        return handler
    
    def register_timeout_guard(self, guard_instance):
        """Wire timeout guard to failure registration."""
        print(f"[SIGNAL] Registering timeout storm guard handler...")
        
        def handler(message, level=1):
            with self.lock:
                print(f"[SIGNAL] TIMEOUT_STORM detected: {message}")
                # Check for timeout patterns
                if 'TIMEOUT_STORM' in message or 'timeout' in message.lower():
                    if self.orchestrator.config.get('timeout_guard.enabled', False):
                        failure_registration.register_failure(
                            event_id='TIMEOUT_STORM',
                            severity='HIGH',
                            message=message,
                            level=level
                        )
                        self.orchestrator.metrics.increment('timeout.storm', 1)
                        self.orchestrator.logger.warning(
                            f"Timeout guard triggered: {message}"
                        )
                        for callback in self.callbacks['TIMEOUT_STORM']:
                            callback(message, level)
                return False
        
        self.signal_sources['TIMEOUT_STORM'] = handler
        self.handlers.append(handler)
        return handler
    
    def register_workspace_guard(self, guard_instance):
        """Wire workspace corruption guard to failure registration."""
        print(f"[SIGNAL] Registering workspace corruption guard handler...")
        
        def handler(message, level=1):
            with self.lock:
                print(f"[SIGNAL] PATH_CORRUPTION detected: {message}")
                # Check for corruption patterns
                if 'PATH_CORRUPTION' in message or 'corrupt' in message.lower():
                    if self.orchestrator.config.get('workspace_guard.enabled', False):
                        failure_registration.register_failure(
                            event_id='PATH_CORRUPTION',
                            severity='CRITICAL',
                            message=message,
                            level=level
                        )
                        self.orchestrator.metrics.increment('workspace.corruption', 1)
                        self.orchestrator.logger.error(
                            f"Workspace corruption detected: {message}"
                        )
                        for callback in self.callbacks['PATH_CORRUPTION']:
                            callback(message, level)
                return False
        
        self.signal_sources['PATH_CORRUPTION'] = handler
        self.handlers.append(handler)
        return handler
    
    def register_memory_guard(self, guard_instance):
        """Wire memory pressure guard to failure registration."""
        print(f"[SIGNAL] Registering memory pressure guard handler...")
        
        def handler(message, level=1):
            with self.lock:
                print(f"[SIGNAL] MEMORY_PRESSURE detected: {message}")
                # Check for memory pressure patterns
                if 'MEMORY_PRESSURE' in message or 'memory_pressure' in message.lower():
                    if self.orchestrator.config.get('memory_guard.enabled', False):
                        failure_registration.register_failure(
                            event_id='MEMORY_PRESSURE',
                            severity='HIGH',
                            message=message,
                            level=level
                        )
                        self.orchestrator.metrics.increment('memory.pressure', 1)
                        self.orchestrator.logger.warning(
                            f"Memory pressure detected: {message}"
                        )
                        for callback in self.callbacks['MEMORY_PRESSURE']:
                            callback(message, level)
                return False
        
        self.signal_sources['MEMORY_PRESSURE'] = handler
        self.handlers.append(handler)
        return handler
    
    def register_failure_callback(self, event_id: str, callback: Callable):
        """Register callback for specific failure event."""
        if event_id in self.callbacks:
            self.callbacks[event_id].append(callback)
        return True
    
    def handle_signal(self, signal_source: str, message: str, level: int = 1):
        """Generic signal handler routing to appropriate registration."""
        print(f"[SIGNAL] Received signal: {signal_source}: {message}")
        
        # Route to specific handler
        handler = self.signal_sources.get(signal_source)
        if handler:
            return handler(message, level)
        
        # Default fallback
        with self.lock:
            print(f"[SIGNAL] Unrecognized signal source: {signal_source}")
            return False


class SignalMonitor(threading.Thread):
    """Background thread for monitoring signal sources."""
    
    def __init__(self, handler: SignalHandler, config: dict):
        super().__init__()
        self.handler = handler
        self.config = config
        self.daemon = True
        self.running = True
        
        # Set thread priority for real-time signaling
        if hasattr(threading, 'start'):
            # Python 3.7+ priority hint
            pass
    
    def run(self):
        """Monitor signal sources in background."""
        while self.running:
            try:
                # Check GPU timeout events
                if self.config.get('gpu_guard.enabled', False):
                    gpu_timeout = gpu_timeout_guard.check(self.config)
                    if gpu_timeout:
                        self.handler.handle_signal('GPU_RUNAWAY', gpu_timeout)
                
                # Check timeout storm events
                if self.config.get('timeout_guard.enabled', False):
                    timeout_storm = gpu_timeout_guard.check_timeouts(self.config)
                    if timeout_storm:
                        self.handler.handle_signal('TIMEOUT_STORM', timeout_storm)
                
                # Check workspace corruption events
                if self.config.get('workspace_guard.enabled', False):
                    workspace_issues = workspace_guard.scan(self.config)
                    for issue in workspace_issues:
                        self.handler.handle_signal('PATH_CORRUPTION', issue)
                
                # Check memory pressure events
                if self.config.get('memory_guard.enabled', False):
                    memory_pressure = memory_guard.check(self.config)
                    if memory_pressure:
                        self.handler.handle_signal('MEMORY_PRESSURE', memory_pressure)
                
                # Sleep between checks (adjustable)
                sleep_time = self.config.get('monitor_interval', 5.0)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.handler.orchestrator.logger.error(
                    f"Signal monitor error: {e}",
                    exc_info=True
                )
    
    def stop(self):
        """Stop the monitor thread."""
        self.running = False


class FailureInjector:
    """Controlled failure injection harness for testing."""
    
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance
        self.config = orchestrator_instance.config
        self.injectors = {
            'GPU_SPIKE': self.inject_gpu_spike,
            'TIMEOUT_STORM': self.inject_timeout_storm,
            'PATH_ANOMALY': self.inject_path_anomaly,
            'MEMORY_COMPRESSION': self.inject_memory_compression
        }
    
    def inject_gpu_spike(self, severity: str = 'CRITICAL'):
        """Simulate GPU VRAM runaway event."""
        print(f"[INJECT] Triggering GPU spike simulation: {severity}")
        fake_message = f"GPU_TIMEOUT_VRAM:VRAM_RUNAWAY:VRAM_SPIKE:GPU_RUNAWAY:MEMORY_LIMIT_EXCEEDED:{severity}:CUDA_ERROR_OUT_OF_MEMORY:ERROR"
        # Route through signal handler
        self.orchestrator.signal_handler.handle_signal('GPU_RUNAWAY', fake_message)
        return True
    
    def inject_timeout_storm(self, timeout_seconds: int = 30):
        """Simulate timeout storm event."""
        print(f"[INJECT] Triggering timeout storm simulation: {timeout_seconds}s")
        fake_message = f"TIMEOUT_STORM:timeout_storm:{timeout_seconds}s:TIMEOUT_EXCEEDED:PROCESS_TIMED_OUT:{severity}:PROCESS_TIMEOUT:ERROR"
        self.orchestrator.signal_handler.handle_signal('TIMEOUT_STORM', fake_message)
        return True
    
    def inject_path_anomaly(self, path: str, error_type: str = 'CORRUPTED'):
        """Simulate workspace path anomaly."""
        print(f"[INJECT] Triggering path anomaly simulation: {path}")
        fake_message = f"PATH_CORRUPTION:path_corrupt:{path}:{error_type}:FILE_NOT_FOUND:PERMISSION_DENIED:ERROR"
        self.orchestrator.signal_handler.handle_signal('PATH_CORRUPTION', fake_message)
        return True
    
    def inject_memory_compression(self, pressure_level: str = 'HIGH'):
        """Simulate memory pressure event."""
        print(f"[INJECT] Triggering memory compression simulation: {pressure_level}")
        fake_message = f"MEMORY_PRESSURE:memory_pressure:{pressure_level}:COMPRESSION_TRIGGERED:MEMORY_THRESHOLD_EXCEEDED:ERROR"
        self.orchestrator.signal_handler.handle_signal('MEMORY_PRESSURE', fake_message)
        return True
    
    def inject_all(self):
        """Inject all failure types for stress testing."""
        print("[INJECT] Triggering full stress injection test...")
        self.inject_gpu_spike()
        self.inject_timeout_storm()
        self.inject_path_anomaly('/home/jason2ykk/.openclaw/workspace')
        self.inject_memory_compression()
        print("[INJECT] All failure types injected. Observe orchestrator conflict resolution.")


class SignalIntegrationModule:
    """Main integration module for wiring all signal sources."""
    
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance
        self.handler = SignalHandler(orchestrator_instance)
        self.monitor = None
        self.injector = None
        self._wired = False
    
    def wire_all(self):
        """Wire all signal sources to orchestrator failure registration."""
        print("=" * 60)
        print("🚀 PENTAGON SYSTEM - INTEGRATION WIRING PHASE")
        print("=" * 60)
        
        print("\n[1/4] WIRING GPU TIMEOUT GUARD SIGNAL...")
        gpu_guard = gpu_timeout_guard.load()
        self.handler.register_gpu_guard(gpu_guard)
        
        print("[2/4] WIRING TIMEOUT GUARD SIGNAL...")
        timeout_guard = gpu_timeout_guard.load()
        self.handler.register_timeout_guard(timeout_guard)
        
        print("[3/4] WIRING WORKSPACE GUARD SIGNAL...")
        workspace_guard = workspace_guard.load()
        self.handler.register_workspace_guard(workspace_guard)
        
        print("[4/4] WIRING MEMORY GUARD SIGNAL...")
        memory_guard = memory_guard.load()
        self.handler.register_memory_guard(memory_guard)
        
        print("\n[COMPLETION] All signals wired to orchestrator.")
        print("\n📡 Signal Routing Map:")
        print("   GPU_TIMEOUT → register_failure(GPU_RUNAWAY)")
        print("   TIMEOUT_STORM → register_failure(TIMEOUT_STORM)")
        print("   PATH_CORRUPTION → register_failure(PATH_CORRUPTION)")
        print("   MEMORY_PRESSURE → register_failure(MEMORY_PRESSURE)")
        print("\n⚠️  System Status: OPERATIONAL (Signal Integration Complete)")
        print("=" * 60)
        
        self._wired = True
        return True
    
    def start_monitor(self, interval: float = 5.0):
        """Start background signal monitor thread."""
        print("[MONITOR] Starting signal monitor thread...")
        self.config = config_reader.load()
        self.monitor = SignalMonitor(self.handler, self.config)
        self.monitor.interval = interval
        self.monitor.start()
        return True
    
    def start_injector(self):
        """Initialize failure injection harness."""
        self.injector = FailureInjector(self.orchestrator)
        return self.injector
    
    def is_wired(self):
        """Check if integration is complete."""
        return self._wired


# Main entry point for integration wiring
def run_integration_wiring(orchestrator_instance):
    """Execute full integration wiring."""
    try:
        integration = SignalIntegrationModule(orchestrator_instance)
        integration.wire_all()
        integration.start_monitor()
        injector = integration.start_injector()
        
        print("\n✅ INTEGRATION WIRING COMPLETE")
        print("   Ready for Phase 1 Real-World Stability Test")
        return True, integration, injector
        
    except Exception as e:
        print(f"[ERROR] Integration wiring failed: {e}")
        return False, None, None


if __name__ == '__main__':
    # Test integration wiring
    from integration import orchestrator
    
    # Initialize orchestrator
    orchestrator_instance = orchestrator.main()
    
    # Run wiring
    success, integration, injector = run_integration_wiring(orchestrator_instance)
    
    if success:
        print("\n🎉 Pentagon System integration wiring complete!")
        print("   Ready for operational deployment.")
    else:
        print("\n❌ Integration wiring failed.")
        sys.exit(1)
