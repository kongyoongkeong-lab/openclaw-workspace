"""
DETERMINISTIC SCHEDULER (G1 Phase 3 Compliant)
============================================

INVARANTS (Non-Negotiable):
1. Pure execution dispatcher ONLY
2. No decision-making
3. No queue governance
4. Deterministic FIFO/priority execution
5. Obeys UCG policy signals ONLY
6. No imports from governance modules

This module is a DUMB PIPE. It executes tasks in deterministic order.
"""

import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from collections import deque


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------

SCHEDULER_ID = "scheduler"
DEFAULT_PRIORITY = "normal"

# Priority levels (for deterministic ordering only):
#   high = 0, normal = 1, low = 2
PRIORITY_MAP = {
    "high": 0,
    "normal": 1,
    "low": 2
}


def _generate_task_id() -> str:
    """Generate unique task ID."""
    return f"task_{uuid.uuid4().hex[:8]}"


def _get_current_timestamp() -> str:
    """Return ISO timestamp."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


# ------------------------------------------------------------------
# PUBLIC API (Execution-Only Interface)
# ------------------------------------------------------------------

def enqueue(task_id: Optional[str] = None, priority: str = DEFAULT_PRIORITY,
            handler: Optional[Callable] = None, data: Optional[Dict[str, Any]] = None) -> str:
    """
    Enqueue a task for deterministic execution.
    
    PARAMS:
        task_id: Unique task identifier (auto-generated if None)
        priority: Priority level ("high", "normal", "low")
        handler: Task handler function
        data: Task payload/data
    
    RETURNS:
        Task ID
    
    INVARIANT: Pure enqueue, no decision-making.
    """
    if task_id is None:
        task_id = _generate_task_id()
    
    task = {
        "task_id": task_id,
        "timestamp": _get_current_timestamp(),
        "priority": priority,
        "handler": handler,
        "data": data or {},
        "status": "queued"
    }
    
    # Store in task registry (no decision logic)
    _register_task(task)
    
    return task_id


def dequeue() -> Optional[Dict[str, Any]]:
    """
    Dequeue the next task based on priority (deterministic order).
    
    PARAMS:
        None
    
    RETURNS:
        Next task dict or None if queue empty
    
    INVARIANT: FIFO/priority execution only, no decision-making.
    """
    # Get registered tasks and sort by priority
    tasks = _get_registered_tasks()
    
    if not tasks:
        return None
    
    # Sort by priority (high=0, normal=1, low=2) for deterministic execution
    tasks.sort(key=lambda t: PRIORITY_MAP.get(t["priority"], 1))
    
    # Return highest priority task
    task = tasks.pop(0)
    task["status"] = "executing"
    
    return task


def run_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a task deterministically.
    
    PARAMS:
        task: Task dict from dequeue()
    
    RETURNS:
        Task result dict
    
    INVARIANT: Pure execution, no decision-making.
    """
    if task["handler"] is None:
        return {
            "task_id": task["task_id"],
            "status": "error",
            "error": "No handler specified",
            "timestamp": _get_current_timestamp()
        }
    
    try:
        result = task["handler"](task["data"])
        
        return {
            "task_id": task["task_id"],
            "status": "completed",
            "result": result,
            "timestamp": _get_current_timestamp()
        }
    
    except Exception as e:
        return {
            "task_id": task["task_id"],
            "status": "failed",
            "error": str(e),
            "timestamp": _get_current_timestamp()
        }


def process_queue(max_tasks: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Process queued tasks deterministically.
    
    PARAMS:
        max_tasks: Maximum tasks to process (None = all)
    
    RETURNS:
        List of execution results
    
    INVARIANT: Deterministic FIFO execution, no decision-making.
    """
    results = []
    
    task = dequeue()
    while task is not None:
        if max_tasks is not None and len(results) >= max_tasks:
            break
        
        result = run_task(task)
        results.append(result)
        task = dequeue()
    
    return results


def get_queue_length() -> int:
    """
    Return current queue length.
    
    INVARIANT: Count-only metric, no scoring.
    """
    return len(_get_registered_tasks())


def clear_queue() -> int:
    """
    Clear all queued tasks.
    
    RETURNS:
        Number of tasks cleared
    
    INVARIANT: Pure cleanup, no decision-making.
    """
    tasks = _get_registered_tasks()
    # In production, this would actually clear the queue
    # For now, just return count
    return len(tasks)


def _register_task(task: Dict[str, Any]) -> None:
    """
    Register a task in the scheduler (internal).
    
    PARAMS:
        task: Task dict
    
    INVARIANT: Pure storage, no decision-making.
    """
    # In production, use a thread-safe queue
    # For now, store in registry
    global _task_registry
    if "_task_registry" not in globals():
        _task_registry = deque()
    
    _task_registry.append(task)


def _get_registered_tasks() -> List[Dict[str, Any]]:
    """
    Get registered tasks (internal).
    
    RETURNS:
        List of task dicts
    
    INVARIANT: Pure retrieval, no decision-making.
    """
    global _task_registry
    if "_task_registry" not in globals():
        return []
    
    return list(_task_registry)


# ------------------------------------------------------------------
# TASK HANDLER REGISTRY (Simple Handler System)
# ------------------------------------------------------------------

def register_handler(name: str, handler: Callable) -> None:
    """
    Register a named task handler.
    
    PARAMS:
        name: Handler name
        handler: Callable function
    
    INVARIANT: Pure registration, no decision-making.
    """
    global _handlers
    if "_handlers" not in globals():
        _handlers = {}
    
    _handlers[name] = handler


def get_handler(name: str) -> Optional[Callable]:
    """
    Get registered handler.
    
    PARAMS:
        name: Handler name
    
    RETURNS:
        Handler function or None
    
    INVARIANT: Pure retrieval, no decision-making.
    """
    global _handlers
    if "_handlers" not in globals():
        return None
    
    return _handlers.get(name)


# Default handlers
def default_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default task handler (placeholder).
    
    PARAMS:
        data: Task data
    
    RETURNS:
        Default result
    
    INVARIANT: Pure execution, no decision-making.
    """
    return {
        "processed": True,
        "data": data,
        "timestamp": _get_current_timestamp()
    }


register_handler("default", default_handler)


# ------------------------------------------------------------------
# PUBLIC API EXPOSITION
# ------------------------------------------------------------------

__all__ = [
    "enqueue",
    "dequeue",
    "run_task",
    "process_queue",
    "get_queue_length",
    "clear_queue",
    "register_handler",
    "get_handler",
]
