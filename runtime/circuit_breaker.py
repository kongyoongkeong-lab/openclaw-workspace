#!/usr/bin/env python3
"""
circuit_breaker.py
Purpose: Prevent retry storms, recursive tool loops, model fallback cascades.
Implements CLOSED -> OPEN -> HALF_OPEN state machine.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

# Configuration
DEFAULT_FAILURE_THRESHOLD = 5        # N failures before opening
DEFAULT_RECOVERY_TIMEOUT = 60        # Seconds before half-open
DEFAULT_SUCCESS_THRESHOLD = 3        # Successes in half-open to close
DEFAULT_TIMEOUT = 30                # Default call timeout

class CircuitBreaker:
    """
    Circuit breaker with failure classification.
    """
    
    def __init__(self, name: str, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
                 recovery_timeout: int = DEFAULT_RECOVERY_TIMEOUT,
                 success_threshold: int = DEFAULT_SUCCESS_THRESHOLD):
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.calls = 0
        self.rejected = 0
        self._callbacks = []
    
    def record_success(self):
        """Record a successful call."""
        self.state = CircuitState.CLOSED
        self.success_count += 1
        self.failure_count = 0
        self.calls += 1
        logger.debug(f"{self.name}: success (state=CLOSED, success_count={self.success_count})")
    
    def record_failure(self, failure_type: str = "general"):
        """
        Record a failure with classification.
        
        Args:
            failure_type: Classification (e.g., 'timeout', 'recursive', 'gpu_pressure')
        """
        self.calls += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        # Immediate open for critical failures (recursive path mutation)
        if failure_type == 'recursive':
            self.state = CircuitState.OPEN
            logger.warning(f"{self.name}: {failure_type} failure (state=CLOSED->OPEN, immediate)")
            return
        
        # Check recovery timeout
        if self._should_open():
            self.state = CircuitState.OPEN
            logger.warning(f"{self.name}: exceeded failure threshold (state=CLOSED->OPEN)")
    
    def _should_open(self) -> bool:
        """Check if circuit should open (after recovery timeout)."""
        if self.failure_count >= self.failure_threshold:
            return True
        return False
    
    def _should_attempt(self) -> bool:
        """Check if call should be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._recovery_elapsed():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"{self.name}: recovery elapsed (state=OPEN->HALF_OPEN)")
                return True
            else:
                logger.debug(f"{self.name}: blocked (state=OPEN, elapsed={self._elapsed_time()}s)")
                self.rejected += 1
                return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow one call in half-open state
            return True
        return False
    
    def _recovery_elapsed(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _elapsed_time(self) -> float:
        """Time since last failure."""
        if self.last_failure_time is None:
            return 0
        return time.time() - self.last_failure_time
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        """
        if not self._should_attempt():
            raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            failure_type = self._classify_failure(e)
            self.record_failure(failure_type)
            raise
    
    def _classify_failure(self, e: Exception) -> str:
        """
        Classify failure type for circuit breaker logic.
        
        Args:
            e: Exception instance
        
        Returns:
            Failure type string
        """
        msg = str(e).lower()
        
        # Recursive path mutation (immediate break)
        if any(term in msg for term in ['recursion', 'stack overflow', 'max depth']):
            return 'recursive'
        
        # GPU pressure (throttle instead of break)
        if any(term in msg for term in ['gpu', 'vram', 'out of memory']):
            return 'gpu_pressure'
        
        # Transient network timeout (retry OK)
        if any(term in msg for term in ['timeout', 'connection refused', 'network', 'network error']):
            return 'timeout'
        
        # General failure
        return 'general'
    
    def reset(self):
        """Reset circuit breaker to initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"{self.name}: reset to CLOSED")
    
    def add_callback(self, callback: Callable):
        """Add callback for circuit state change."""
        self._callbacks.append(callback)
        self._notify_callbacks()
    
    def _notify_callbacks(self):
        """Notify callbacks of state change."""
        for cb in self._callbacks:
            try:
                cb(self.state)
            except Exception as e:
                logger.error(f"Callback failed: {e}")

# Global circuit breakers
_breakers: Dict[str, CircuitBreaker] = {
    'inference': CircuitBreaker('inference'),
    'web_search': CircuitBreaker('web_search'),
    'memory_read': CircuitBreaker('memory_read'),
    'file_io': CircuitBreaker('file_io'),
}

def get_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name)
    return _breakers[name]

__all__ = ['CircuitState', 'CircuitBreaker', '_breakers', 'get_breaker']
