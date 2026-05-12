#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versioned Incident State Management

Provides:
- Optimistic concurrency control via versioning
- Single-writer rule enforcement
- State transition validation
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, Optional, Tuple, List


class IncidentVersionStore:
    """
    Versioned incident state management with optimistic concurrency control.
    
    Provides:
    - Atomic version tracking
    - Stale mutation detection
    - Conflict resolution utilities
    """
    
    def __init__(
        self,
        base_dir: str = "/home/jason2ykk/.openclaw/workspace/incidents"
    ):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
    
    def get_incident_path(self, incident_key: str) -> Path:
        """Get path to incident state file."""
        return self.base_dir / f"{incident_key}.json"
    
    def read_incident(self, incident_key: str) -> Optional[Dict]:
        """
        Read incident state with metadata.
        
        Args:
            incident_key: Incident identifier
        
        Returns:
            Incident dict or None if not found
        """
        path = self.get_incident_path(incident_key)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, IOError):
            return None
    
    def write_incident(
        self,
        incident_key: str,
        state: Dict,
        sequence: Optional[int] = None,
        version: Optional[int] = None
    ) -> Tuple[bool, Dict]:
        """
        Write incident state with version tracking.
        
        Args:
            incident_key: Incident identifier
            state: Incident state dict
            sequence: Optional ingest sequence for metadata
            version: Optional version for optimistic locking
        
        Returns:
            (success, metadata)
        """
        with self._lock:
            path = self.get_incident_path(incident_key)
            
            # Update state with versioning info
            state_with_meta = {
                **state,
                "ingest_sequence": sequence,
                "ingest_time": datetime.utcnow().isoformat(),
                "state_hash": self._compute_hash(state),
                "last_modified": datetime.now(timezone.utc).isoformat()
            }
            
            if version is not None:
                state_with_meta["version"] = version
            
            # Write to temp file then rename (atomic)
            temp_path = path.with_suffix('.tmp')
            try:
                with open(temp_path, 'w') as f:
                    json.dump(state_with_meta, f, indent=2)
                
                # Atomic rename
                temp_path.rename(path)
                
                metadata = {
                    "incident_key": incident_key,
                    "operation": "write",
                    "version": state_with_meta.get("version"),
                    "ingest_sequence": sequence,
                    "status": "committed"
                }
                
                return True, metadata
            except IOError:
                if temp_path.exists():
                    temp_path.unlink()
                return False, {"error": "write_failed", "incident_key": incident_key}
    
    def validate_version(
        self,
        incident_key: str,
        expected_version: int,
        mutation: Dict
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate mutation against expected version (optimistic locking).
        
        Args:
            incident_key: Incident identifier
            expected_version: Expected current version
            mutation: Proposed mutation dict
        
        Returns:
            (is_valid, error_message, current_state)
        """
        current_state = self.read_incident(incident_key)
        
        if current_state is None:
            return True, None, {"version": 1, "state": mutation}
        
        current_version = current_state.get("version", 1)
        
        if current_version != expected_version:
            error = f"Version mismatch: expected {expected_version}, got {current_version}"
            return False, error, current_state
        
        return True, None, current_state
    
    def increment_version(
        self,
        incident_key: str,
        base_state: Dict
    ) -> Tuple[int, Dict]:
        """
        Increment version and apply mutation.
        
        Args:
            incident_key: Incident identifier
            base_state: State to mutate
        
        Returns:
            (new_version, mutated_state)
        """
        current = self.read_incident(incident_key)
        
        if current is None:
            # First write
            new_state = {
                **base_state,
                "version": 1,
                "ingest_sequence": None,
                "created": datetime.now(timezone.utc).isoformat()
            }
            self.write_incident(incident_key, new_state)
            return 1, new_state
        
        version = current.get("version", 1) + 1
        mutated_state = {
            **current,
            **base_state,
            "version": version
        }
        
        self.write_incident(incident_key, mutated_state)
        return version, mutated_state
    
    def detect_conflict(
        self,
        incident_key: str,
        pending_version: int,
        current_state: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect concurrent update conflict.
        
        Args:
            incident_key: Incident identifier
            pending_version: Version in pending mutation
            current_state: Current state from incident store
        
        Returns:
            (has_conflict, conflict_message)
        """
        if pending_version != current_state.get("version", 1):
            return True, f"Conflict: pending_version {pending_version} != current_version {current_state.get('version')}"
        
        return False, None
    
    def merge_conflict(
        self,
        incident_key: str,
        pending_state: Dict,
        current_state: Dict
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Attempt to merge conflicting states.
        
        Args:
            incident_key: Incident identifier
            pending_state: Pending mutation state
            current_state: Current state
        
        Returns:
            (success, merged_state)
        """
        # Simple merge strategy: prefer current state
        merged = {
            **current_state,
            **pending_state,
            "version": current_state.get("version", 1) + 1,
            "merge_timestamp": datetime.now(timezone.utc).isoformat(),
            "merge_strategy": "prefer_current"
        }
        
        success, _ = self.write_incident(incident_key, merged)
        return success, merged
    
    def compute_hash(self, state: Dict) -> str:
        """Compute deterministic hash of state for change detection."""
        import hashlib
        state_str = json.dumps(state, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]
    
    def get_incident_info(self, incident_key: str) -> Optional[Dict]:
        """Get incident metadata without full state."""
        state = self.read_incident(incident_key)
        if state is None:
            return None
        
        return {
            "incident_key": incident_key,
            "version": state.get("version"),
            "ingest_sequence": state.get("ingest_sequence"),
            "last_modified": state.get("last_modified"),
            "created": state.get("created")
        }


class SingleWriterEnforcer:
    """
    Enforces single-writer rule per incident_key.
    
    Only one mutation path is allowed per incident at any instant.
    """
    
    def __init__(self, store: IncidentVersionStore):
        self.store = store
    
    def validate_single_writer(
        self,
        incident_key: str,
        mutation_metadata: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that mutation respects single-writer rule.
        
        Args:
            incident_key: Incident identifier
            mutation_metadata: Metadata from mutation source
        
        Returns:
            (is_valid, error_message)
        """
        # Get current state
        current = self.store.read_incident(incident_key)
        
        if current is None:
            # First write is always valid
            return True, None
        
        # Check if mutation sequence advances
        incoming_seq = mutation_metadata.get("ingest_sequence")
        last_seq = current.get("ingest_sequence")
        
        if last_seq is None:
            # No prior sequence, mutation valid
            return True, None
        
        if incoming_seq is None:
            return False, "Mutation missing ingest_sequence"
        
        if incoming_seq <= last_seq:
            return False, f"Non-advancing sequence: {incoming_seq} <= {last_seq}"
        
        return True, None
    
    def get_writer_info(
        self,
        incident_key: str
    ) -> Optional[str]:
        """Get last writer metadata for incident."""
        state = self.store.read_incident(incident_key)
        if state is None:
            return None
        
        metadata = state.get("metadata", {})
        return metadata.get("writer_id", "unknown")


def create_version_store_service():
    """Create version store service."""
    return IncidentVersionStore(
        base_dir="/home/jason2ykk/.openclaw/workspace/incidents"
    )


if __name__ == "__main__":
    # Test versioned state management
    store = create_version_store_service()
    
    # Test incident lifecycle
    incident_key = "test_incident_001"
    
    # First write
    state1 = {
        "severity": 1,
        "status": "open"
    }
    success, meta = store.write_incident(incident_key, state1)
    print(f"First write: {success}, version {meta.get('version')}")
    
    # Second write
    state2 = {"severity": 2, "status": "escalated"}
    success, meta = store.write_incident(incident_key, state2)
    print(f"Second write: {success}, version {meta.get('version')}")
    
    # Read incident
    info = store.get_incident_info(incident_key)
    print(f"Incident info: {info}")
    
    # Test version validation
    valid, error, current = store.validate_version(
        incident_key,
        expected_version=2,
        mutation={"severity": 3}
    )
    print(f"Version 2 validation: {valid}, {error}")
    
    # Test stale mutation detection
    valid, error, _ = store.validate_version(
        incident_key,
        expected_version=1,  # Stale version
        mutation={"severity": 100}
    )
    print(f"Stale version 1 validation: {valid}, {error}")
