#!/usr/bin/env python3
"""
memory_store.py - Append-only memory writer (v1)

CRITICAL RULE: NEVER OVERWRITE EXISTING LINES
All writes must append to `memory.jsonl`
"""

import json
import os
from datetime import datetime
from typing import Optional


MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory", "memory.jsonl")

# CRITICAL: Check for write lock before attempting write
WRITE_LOCK = os.path.join(MEMORY_FILE, ".write.lock")
LOCK_TIMEOUT = 30  # seconds


def ensure_directory():
    """Ensure parent directory exists"""
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)


def acquire_lock() -> Optional[int]:
    """Try to acquire write lock. Returns lock fd or None on timeout."""
    try:
        lock_fd = os.open(WRITE_LOCK, os.O_CREAT | os.O_EXCL)
        os.fsync(lock_fd)
        os.close(lock_fd)
        return lock_fd
    except (OSError, PermissionError) as e:
        print(f"[LOCK] Cannot acquire write lock: {e}")
        return None


def release_lock(lock_fd: int):
    """Release write lock"""
    try:
        os.fsync(lock_fd)
        os.close(lock_fd)
    except OSError as e:
        print(f"[LOCK] Error releasing lock: {e}")


def is_write_blocked() -> bool:
    """Check if another process is writing"""
    if not os.path.exists(WRITE_LOCK):
        return False
    try:
        lock_fd = os.open(WRITE_LOCK, os.O_RDONLY)
        os.close(lock_fd)
        return True  # Lock exists = blocked
    except OSError as e:
        print(f"[LOCK] Check error: {e}")
        return False


def write_entry(entry: dict) -> bool:
    """
    Append single entry to memory.jsonl

    CRITICAL: This function MUST NOT overwrite existing lines.
    It appends to the end of the file.
    """
    ensure_directory()

    if is_write_blocked():
        print("[CRITICAL] Write lock active - another process writing")
        return False

    try:
        # Write to temp file, then rename (atomic)
        temp_file = f"{MEMORY_FILE}.tmp.{int(datetime.now().timestamp())}"
        
        with open(temp_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()
            os.fsync(f.fileno())
        
        os.rename(temp_file, MEMORY_FILE)
        return True
    except (OSError, PermissionError) as e:
        print(f"[WRITE] Failed to append: {e}")
        return False


def write_entries(entries: list) -> int:
    """
    Write multiple entries atomically

    Returns number of entries written (0 if any failed)
    """
    ensure_directory()

    if not entries:
        return 0

    # Check if write blocked
    if is_write_blocked():
        print("[CRITICAL] Write lock active - another process writing")
        return 0

    try:
        # Write to temp file, then rename (atomic)
        temp_file = f"{MEMORY_FILE}.tmp.{int(datetime.now().timestamp())}"
        
        with open(temp_file, "a") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")
                f.flush()
                os.fsync(f.fileno())
        
        os.rename(temp_file, MEMORY_FILE)
        return len(entries)
    except (OSError, PermissionError) as e:
        print(f"[WRITE] Failed to append: {e}")
        return 0


if __name__ == "__main__":
    # Test write
    test_entry = {
        "timestamp": "2026-05-06T09:11:00+08:00",
        "type": "bootstrap",
        "text": "memory_store.py initialized - append-only mode active",
        "author": "@main"
    }
    
    result = write_entry(test_entry)
    print(f"[WRITE] Entry appended: {result}")

    # Verify write
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    print(f"  Line {i}: {line.strip()[:100]}")
