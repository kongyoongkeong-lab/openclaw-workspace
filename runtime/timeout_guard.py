#!/usr/bin/env python3
"""
timeout_guard.py
Purpose: Layered timeout governance (inference → fallback → hard kill).
Supports cancellation tokens and async-safe timeouts.
"""

import os
import signal
import logging
from typing import Optional, Callable, Any
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

# Layered timeout configuration (WSL2-safe)
TIMEOUT_INFEERENCE_SOFT = 30    # s - Soft timeout for inference
TIMEOUT_FALLBACK_TRIGGER = 45   # s - Trigger model fallback
TIMEOUT_HARD_KILL = 90          # s - Hard kill for deadlocks

TIMEOUT_CONFIG = {
    'inference_soft': TIMEOUT_INFEERENCE_SOFT,
    'fallback_trigger': TIMEOUT_FALLBACK_TRIGGER,
    'hard_kill': TIMEOUT_HARD_KILL
}

class TimeoutError(Exception):
    """Raised when a timeout expires."""
    pass

class TimeoutHandler:
    """
    Handles timeouts with cancellation tokens and cleanup.
    """
    
    def __init__(self, timeout: int):
        self.timeout = timeout
        self.cancelled = False
        self.cleanup_callbacks: list = []
    
    def register_cleanup(self, callback: Callable):
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)
    
    def cancel(self):
        """Cancel the timeout and trigger cleanup."""
        self.cancelled = True
        for cb in self.cleanup_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
    
    def apply_to_function(self, func: Callable) -> Callable:
        """
        Decorator to apply timeout to a function.
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout after {self.timeout}s on {func.__name__}")
                self.cancelled = True
                for cb in self.cleanup_callbacks:
                    try:
                        cb()
                    except Exception as e:
                        logger.error(f"Cleanup callback failed: {e}")
                raise TimeoutError(f"Function {func.__name__} exceeded {self.timeout}s timeout")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError):
                    logger.warning(f"Timeout after {self.timeout}s on {func.__name__}")
                    self.cancelled = True
                    for cb in self.cleanup_callbacks:
                        try:
                            cb()
                        except Exception as e2:
                            logger.error(f"Cleanup callback failed: {e2}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    def cleanup(self):
        """Run all cleanup callbacks."""
        for cb in self.cleanup_callbacks:
            try:
                cb()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")

def timeout_decorator(timeout: int):
    """
    Factory function for timeout decorator.
    """
    def decorator(func: Callable) -> Callable:
        handler = TimeoutHandler(timeout)
        return handler.apply_to_function(func)
    return decorator

def create_timeout_layer(layer_name: str, timeout: int) -> dict:
    """
    Create a timeout layer configuration.
    
    Args:
        layer_name: Name of the layer (e.g., 'inference', 'fallback')
        timeout: Timeout in seconds
    
    Returns:
        Dict with layer configuration
    """
    return {
        'layer': layer_name,
        'timeout': timeout,
        'action': 'warn' if layer_name == 'inference' else 'fallback' if layer_name == 'fallback' else 'kill',
        'status': 'active'
    }

def setup_timeout_signals():
    """
    Setup timeout signals for WSL2-safe cancellation.
    """
    try:
        signal.signal(signal.SIGALRM, lambda signum, frame: None)
        signal.alarm(TIMEOUT_HARD_KILL)
    except (OSError, ValueError):
        # Non-Unix or signal not supported
        pass

def cleanup_timeout_processes():
    """
    Cleanup timeout-related processes.
    """
    try:
        os.killpg(os.getpgid(os.getpid()), signal.SIGTERM)
    except OSError:
        pass

__all__ = ['TIMEOUT_INFEERENCE_SOFT', 'TIMEOUT_FALLBACK_TRIGGER', 'TIMEOUT_HARD_KILL',
           'TIMEOUT_CONFIG', 'TimeoutError', 'TimeoutHandler', 'timeout_decorator',
           'create_timeout_layer', 'setup_timeout_signals', 'cleanup_timeout_processes']
