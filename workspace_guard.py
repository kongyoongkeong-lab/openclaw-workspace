#!/usr/bin/env python3
"""
workspace_guard.py
==================
Canonical Workspace Authority Enforcement Layer

Responsibilities:
- Canonical root enforcement
- Nested workspace detection
- Path traversal rejection
- Identity drift prevention (jason vs jason2ykk)

This is the highest historical corruption vector guard.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional, Tuple


class WorkspaceGuard:
    """Workspace authority enforcement with identity drift prevention."""

    # Canonical workspace patterns
    CANONICAL_ROOTS = [
        Path("/home/jason/.openclaw/workspace"),
        Path("/home/jason2ykk/.openclaw/workspace"),
    ]

    # Workspace identity markers
    IDENTITY_MARKER = "IDENTITY.md"
    CANONICAL_MARKER = ".canonical"

    # Path traversal patterns
    TRAVERSAL_PATTERNS = [r"\.\.", r"\.\./", r"/\.\./"]

    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize with explicit workspace root.

        Args:
            workspace_root: Explicit path override. If None, reads from IDENTITY.md
        """
        if workspace_root is None:
            # Read canonical root from IDENTITY.md if present
            self.canonical_root = self._read_canonical_root()
        else:
            self.canonical_root = Path(workspace_root)

        # Identity lock
        self.identity_drifted = False
        self.drift_reason: Optional[str] = None

    def _read_canonical_root(self) -> Path:
        """Read canonical root from IDENTITY.md (if present)."""
        for root in self.CANONICAL_ROOTS:
            identity_file = root / self.IDENTITY_MARKER
            if identity_file.exists():
                try:
                    content = identity_file.read_text()
                    # Extract canonical root from IDENTITY.md
                    match = re.search(
                        r"Path Configuration:[^]*?\n- *Correct Base:\s*(.+)",
                        content,
                        re.IGNORECASE | re.MULTILINE
                    )
                    if match:
                        root_str = match.group(1).strip()
                        return Path(root_str)
                except Exception:
                    continue
        # Default to first available canonical root
        for root in self.CANONICAL_ROOTS:
            if root.exists():
                return root
        raise RuntimeError(
            "No canonical workspace root found. "
            "Please configure IDENTITY.md in your workspace."
        )

    def validate_workspace_root(self, path: str) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Validate that a workspace path is canonical.

        Args:
            path: Path to validate

        Returns:
            Tuple of (is_valid, canonical_path, error_message)
        """
        path_obj = Path(path)

        # Check for path traversal
        if self._has_traversal(path):
            return False, None, "Path traversal detected (../ or similar)"

        # Check for nested workspace (workspace inside workspace)
        if self._is_nested_workspace(path_obj):
            return False, None, "Nested workspace detected. Use canonical root only."

        # Check against canonical roots
        for root in self.CANONICAL_ROOTS:
            if path_obj == root:
                return True, root, None

            # Normalize paths for comparison
            try:
                resolved_path = path_obj.resolve(strict=False)
                if resolved_path == root.resolve():
                    return True, root, None
            except (OSError, ValueError):
                continue

        # Path is not canonical
        return False, None, f"Path '{path}' is not a recognized canonical workspace root"

    def _has_traversal(self, path: str) -> bool:
        """Check if path contains traversal patterns."""
        for pattern in self.TRAVERSAL_PATTERNS:
            if re.search(pattern, path):
                return True
        return False

    def _is_nested_workspace(self, path: Path) -> bool:
        """Check if this path is a workspace nested inside another workspace."""
        for root in self.CANONICAL_ROOTS:
            try:
                resolved = path.resolve(strict=False)
                root_resolved = root.resolve()
                if root_resolved in resolved.parents:
                    return True
            except (OSError, ValueError):
                continue
        return False

    def read_identity(self) -> dict:
        """Read workspace identity from IDENTITY.md."""
        identity_file = self.canonical_root / self.IDENTITY_MARKER
        if not identity_file.exists():
            return {}

        content = identity_file.read_text()
        identity = {
            "roots": [],
            "model": "qwen3.5:9b",
        }

        # Extract paths
        for root in self.CANONICAL_ROOTS:
            identity_file_test = root / self.IDENTITY_MARKER
            if identity_file_test.exists():
                identity["roots"].append(str(root))

        identity["workspace"] = str(self.canonical_root)

        return identity

    def check_identity_drift(self, path: str) -> bool:
        """
        Check if the given path shows signs of identity drift.

        Args:
            path: Path to check

        Returns:
            True if drift detected, False otherwise
        """
        path_obj = Path(path)
        self.identity_drifted = False

        for root in self.CANONICAL_ROOTS:
            identity_file = root / self.IDENTITY_MARKER
            if not identity_file.exists():
                continue

            try:
                content = identity_file.read_text()
                if path_obj == root or (path_obj.resolve(strict=False) == root.resolve()):
                    # This is a canonical root - OK
                    self.identity_drifted = False
                    return False

                # Check if path points to different user home
                home_path = Path("/home") / path_obj.parent.parts[-2] if path_obj.exists() else None
                if home_path and home_path.parts[-1] in ["jason", "jason2ykk"]:
                    self.identity_drifted = True
                    self.drift_reason = f"Identity drift detected: path points to {home_path}, expected {self.canonical_root}"
                    return True
            except Exception:
                continue

        return False

    def enforce_canonical_root(self) -> Path:
        """
        Enforce canonical workspace root.

        Returns:
            Canonical workspace root path

        Raises:
            RuntimeError: If no canonical root is available
        """
        if not self.canonical_root.exists():
            # Try to bootstrap
            self._bootstrap_canonical_root()

        return self.canonical_root

    def _bootstrap_canonical_root(self) -> Path:
        """Bootstrap canonical root if missing."""
        # Create minimal IDENTITY.md if missing
        identity_file = self.canonical_root / self.IDENTITY_MARKER
        if not identity_file.exists():
            identity_content = """# Workspace Identity: Canonical Root
**Status:** Initializing canonical workspace authority.

## Path Configuration
- Correct Base: /home/jason/.openclaw/workspace

## Identity Lock
- Model: qwen3.5:9b
- Guardian: @sentinel
- Runtime: governed

## Guard
- Nested workspace detection: ACTIVE
- Path traversal rejection: ACTIVE
- Identity drift prevention: ACTIVE
"""
            identity_file.write_text(identity_content)
            self.canonical_root = self.canonical_root / self.IDENTITY_MARKER

        return self.canonical_root

    def validate_write_path(self, write_path: str, allow_relative: bool = False) -> Tuple[bool, str]:
        """
        Validate a write path before file operations.

        Args:
            write_path: Path to validate
            allow_relative: If True, resolve relative to canonical root

        Returns:
            Tuple of (is_valid, message)
        """
        path_obj = Path(write_path)

        # If relative path, resolve to canonical root
        if not path_obj.is_absolute() and allow_relative:
            try:
                # Check if relative path is inside canonical root
                canonical_resolved = self.canonical_root.resolve()
                if path_obj.resolve(strict=False) in canonical_resolved.parents or path_obj.resolve(strict=False) == canonical_resolved:
                    return True, f"Path resolved to canonical root: {self.canonical_root}"
                else:
                    return False, f"Path '{write_path}' is outside canonical root: {self.canonical_root}"
            except (OSError, ValueError):
                return False, f"Cannot resolve path '{write_path}'"

        # Validate against canonical roots
        is_valid, canonical_path, error = self.validate_workspace_root(write_path)
        return is_valid, error

    def get_workspace_info(self) -> dict:
        """Get workspace information."""
        try:
            resolved = self.canonical_root.resolve()
        except (OSError, ValueError):
            resolved = self.canonical_root

        return {
            "canonical_root": str(resolved),
            "canonical_root_resolved": str(resolved.resolve(strict=False) if resolved.exists() else str(resolved)),
            "identity_marker": str(resolved / self.IDENTITY_MARKER),
            "roots_available": len([r for r in self.CANONICAL_ROOTS if r.exists()]),
            "identity_drifted": self.identity_drifted,
            "drift_reason": self.drift_reason,
        }


def main():
    """Main entry point for CLI testing."""
    print("Workspace Guard v1.0")
    print("=" * 40)

    guard = WorkspaceGuard()

    print(f"Canonical Root: {guard.canonical_root}")
    print(f"Available Roots: {[r for r in guard.CANONICAL_ROOTS if r.exists()]}")

    # Get workspace info
    info = guard.get_workspace_info()
    print(f"\nWorkspace Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test path validation
    test_paths = [
        "/home/jason2ykk/.openclaw/workspace",
        "/home/jason/.openclaw/workspace",
        "/home/jason2ykk/.openclaw/workspace/tools",
        "/home/jason2ykk/.openclaw/workspace/memory",
        "/tmp/workaround",
        "/home/jason2ykk/.openclaw/workspace/../tools",
    ]

    print(f"\nPath Validation Tests:")
    for test_path in test_paths:
        is_valid, message = guard.validate_write_path(test_path)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {test_path}: {message}")

    print("\nWorkspace guard initialized.")


if __name__ == "__main__":
    main()
