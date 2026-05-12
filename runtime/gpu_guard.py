#!/usr/bin/env python3
"""
gpu_guard.py
Purpose: GPU pressure monitor (WSL2-safe).
Throttle inference queue at 85%, reject at 90%.
"""

import os
import subprocess
import json
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

# GPU thresholds (WSL2-safe)
GPU_PRESSURE_WARNING = 80    # warn
GPU_PRESSURE_THROTTLE = 85   # throttle
GPU_PRESSURE_REJECT = 90     # reject new inference

class PressureLevel(Enum):
    NORMAL = "normal"
    WARN = "warn"
    THROTTLE = "throttle"
    REJECT = "reject"

def get_gpu_stats() -> Dict[str, Any]:
    """
    Get GPU statistics via nvidia-smi.
    
    Returns:
        Dict with GPU stats
    """
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-application=used_memory', '--query-compute-application=total_memory', '--query-compute-application=memory_utilization', '--format=csv'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            logger.warning(f"nvidia-smi failed: {result.stderr}")
            return {}
        
        # Parse output
        lines = result.stdout.strip().split('\n')
        stats = {}
        
        for line in lines[1:]:  # Skip header
            parts = line.split(',')
            if len(parts) >= 3:
                try:
                    stats['used_memory'] = int(parts[1])  # MB
                    stats['total_memory'] = int(parts[0])  # MB
                    stats['memory_utilization'] = int(parts[2])  # %
                except (ValueError, IndexError):
                    continue
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get GPU stats: {e}")
        return {}

def get_gpu_pressure_level() -> tuple[PressureLevel, float, Dict]:
    """
    Determine GPU pressure level.
    
    Returns:
        (PressureLevel, utilization_percent, stats)
    """
    stats = get_gpu_stats()
    
    if not stats:
        return PressureLevel.NORMAL, 0.0, {}
    
    util = stats.get('memory_utilization', 0)
    used = stats.get('used_memory', 0)
    total = stats.get('total_memory', 1)  # Avoid div by zero
    
    # Calculate percentage
    utilization_pct = (used / total) * 100 if total > 0 else 0
    
    if utilization_pct >= GPU_PRESSURE_REJECT:
        level = PressureLevel.REJECT
    elif utilization_pct >= GPU_PRESSURE_THROTTLE:
        level = PressureLevel.THROTTLE
    elif utilization_pct >= GPU_PRESSURE_WARNING:
        level = PressureLevel.WARN
    else:
        level = PressureLevel.NORMAL
    
    logger.info(f"GPU pressure: {utilization_pct:.1f}% -> {level.value}")
    return level, utilization_pct, stats

def throttle_inference():
    """
    Throttle inference queue (non-blocking).
    """
    logger.warning("GPU pressure high - throttling inference")
    
    # Add delay to inference queue
    import time
    time.sleep(2)  # Short delay to reduce pressure
    
    return True

def reject_inference(reason: str = "GPU pressure high"):
    """
    Reject new inference request.
    """
    logger.error(f"GPU pressure high - rejecting inference: {reason}")
    return False

def check_gpu_health() -> Dict[str, Any]:
    """
    Comprehensive GPU health check.
    
    Returns:
        Dict with health status
    """
    result = {
        'healthy': True,
        'utilization': 0,
        'used_memory': 0,
        'total_memory': 0,
        'pressure_level': PressureLevel.NORMAL,
        'warnings': []
    }
    
    stats = get_gpu_stats()
    
    if not stats:
        result['healthy'] = False
        result['error'] = 'Failed to get GPU stats'
        return result
    
    utilization_pct = (stats.get('used_memory', 0) / stats.get('total_memory', 1)) * 100
    result['utilization'] = utilization_pct
    result['used_memory'] = stats.get('used_memory', 0)
    result['total_memory'] = stats.get('total_memory', 0)
    
    level, util, _ = get_gpu_pressure_level()
    result['pressure_level'] = level
    result['utilization'] = util
    
    if level == PressureLevel.WARN:
        result['warnings'].append('GPU pressure warning (>=80%)')
    elif level == PressureLevel.THROTTLE:
        result['warnings'].append('GPU pressure throttle (>=85%)')
    elif level == PressureLevel.REJECT:
        result['warnings'].append('GPU pressure reject (>=90%)')
    
    return result

# Singleton guard
_gpu_guard_state = {
    'last_check': None,
    'check_count': 0,
    'throttle_count': 0,
    'reject_count': 0
}

def check_and_report() -> Dict[str, Any]:
    """
    Check GPU health and report.
    Includes cooldown to prevent repeated checks.
    """
    now = time.time()
    cooldown = 30  # seconds between checks
    
    if _gpu_guard_state['last_check'] and (now - _gpu_guard_state['last_check'] < cooldown):
        logger.debug(f"GPU check cooldown active ({now - _gpu_guard_state['last_check']:.1f}s)")
        return _build_report('COOLDOWN')
    
    health = check_gpu_health()
    _gpu_guard_state['last_check'] = now
    _gpu_guard_state['check_count'] += 1
    
    if health['healthy']:
        _gpu_guard_state['throttle_count'] = 0
        _gpu_guard_state['reject_count'] = 0
    
    return health

def _build_report(status: str) -> Dict[str, Any]:
    """Build a status report."""
    return {
        'healthy': True,
        'status': status,
        'utilization': 0,
        'pressure_level': PressureLevel.NORMAL
    }

__all__ = ['get_gpu_stats', 'get_gpu_pressure_level', 'throttle_inference', 'reject_inference', 
           'check_gpu_health', 'check_and_report']
