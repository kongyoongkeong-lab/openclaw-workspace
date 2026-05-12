#!/usr/bin/env python3
"""
workspace_guard.py
Purpose: Enforce canonical workspace root, prevent path drift, reject foreign roots.
"""

import os
from typing import Optional, Dict, Any

# Canonical workspace configuration (WSL2 safe)
CANONICAL_ROOT = "/home/jason2ykk/.openclaw/workspace"
ALLOWED_BASE = os.path.realpath(CANONICAL_ROOT)

# Allowed path patterns (prevent drift)
ALLOWED_PATTERNS = [
    CANONICAL_ROOT,
    f"{CANONICAL_ROOT}/memory",
    f"{CANONICAL_ROOT}/tools",
    f"{CANONICAL_ROOT}/agents",
    f"{CANONICAL_ROOT}/runtime",
]

def is_path_safe(path: str) -> Dict[str, Any]:
    """
    Validate a path against canonical workspace rules.
    
    Returns:
        {
            'valid': bool,
            'path': str,
            'canonical': str,
            'issue': str or None,
            'severity': str or None
        }
    """
    # Normalize path
    real_path = os.path.realpath(path)
    
    # Check if under canonical root
    if not real_path.startswith(ALLOWED_BASE):
        return {
            'valid': False,
            'path': real_path,
            'canonical': ALLOWED_BASE,
            'issue': f"Path outside canonical root: {real_path}",
            'severity': 'CRITICAL'
        }
    
    # Check for nested workspace duplication
    if 'workspace/workspace' in real_path:
        return {
            'valid': False,
            'path': real_path,
            'canonical': ALLOWED_BASE,
            'issue': "Nested workspace duplication detected",
            'severity': 'HIGH'
        }
    
    # Check against allowed patterns
    is_allowed = any(ALLOWED_PATTERNS[p] in real_path for p in ALLOWED_PATTERNS) or \
                real_path.startswith(ALLOWED_BASE)
    
    if not is_allowed and path != ALLOWED_BASE:
        return {
            'valid': False,
            'path': real_path,
            'canonical': ALLOWED_BASE,
            'issue': "Path not in allowed workspace patterns",
            'severity': 'MEDIUM'
        }
    
    return {
        'valid': True,
        'path': real_path,
        'canonical': ALLOWED_BASE,
        'issue': None,
        'severity': None
    }

def validate_workspace_root() -> Dict[str, Any]:
    """
    Validate that the current workspace is at canonical root.
    """
    current = os.getcwd()
    result = is_path_safe(current)
    
    if not result['valid']:
        result['recommendation'] = f"Move to canonical root: {ALLOWED_BASE}"
    
    return result

def sanitize_path(user_path: str) -> Optional[str]:
    """
    Sanitize user-provided path to canonical root if possible.
    Returns None if path is irrecoverable.
    """
    result = is_path_safe(user_path)
    
    if result['valid']:
        # Return normalized canonical path
        return os.path.normpath(user_path)
    
    if result['severity'] == 'CRITICAL':
        return None  # Unsafe path
    
    # For medium issues, warn but allow if user insists
    # (e.g., legacy files under old location)
    return os.path.normpath(user_path)

# Singleton guard instance
_workspace_guard: Optional[Any] = None

def get_guard() -> Any:
    """Lazy singleton guard instance."""
    global _workspace_guard
    if _workspace_guard is None:
        import runtime_guard
        _workspace_guard = runtime_guard.WorkspaceGuard()
    return _workspace_guard

# Export interface
__all__ = ['CANONICAL_ROOT', 'ALLOWED_BASE', 'is_path_safe', 'validate_workspace_root', 'sanitize_path', 'get_guard']
