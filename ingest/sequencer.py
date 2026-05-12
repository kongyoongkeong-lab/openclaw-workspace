#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Ingest Sequencer - Authoritative temporal spine

Dual-time model:
- physical_time: wall clock timestamp (observability)
- logical_time: monotonic ingest sequence (ordering authority)
- source_time: optional remote timestamp (forensics)
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, Optional, Tuple, List


class IngestSequencer:
    """
    Authoritative ingest sequencing for temporal authority.
    
    Provides:
    - Monotonic sequence IDs for ordering
    - Physical time for observability
    - Forensic source time tracking
    """
    
    def __init__(
        self,
        counter_file: str = "/home/jason2ykk/.openclaw/workspace/ingest/sequence",
        timestamp_dir: str = "/home/jason2ykk/.openclaw/workspace/ingest/timestamps"
    ):
        self.counter_file = counter_file
        self._lock = Lock()
        self._sequence = self._load_sequence()
        self._timestamp_dir = Path(timestamp_dir)
        self._timestamp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sequence counter if file doesn't exist
        if not os.path.exists(self.counter_file):
            self._save_sequence(0)
    
    def _load_sequence(self) -> int:
        try:
            with open(self.counter_file, 'r') as f:
                content = f.read().strip()
                return int(content) if content else 0
        except (FileNotFoundError, ValueError):
            return 0
    
    def _save_sequence(self, seq: int):
        with open(self.counter_file, 'w') as f:
            f.write(str(seq))
    
    def get_next_sequence(
        self,
        physical_time: Optional[datetime] = None,
        source_time: Optional[datetime] = None
    ) -> Tuple[int, Dict[str, str]]:
        """
        Get next monotonic sequence ID with temporal metadata.
        
        Args:
            physical_time: Wall clock timestamp (wall-clock timezone)
            source_time: Optional remote timestamp from ingestion source
        
        Returns:
            Tuple of (sequence, metadata_dict)
        """
        if physical_time is None:
            physical_time = datetime.now(timezone.utc)
        
        with self._lock:
            self._sequence += 1
            self._save_sequence(self._sequence)
            
            # Generate physical timestamp file for this sequence
            physical_ts = physical_time.replace(tzinfo=None) if physical_time.tzinfo else physical_time
            seq_file = self._timestamp_dir / f"{self._sequence:08d}.tsv"
            
            metadata = {
                "physical_time": physical_time.isoformat(),
                "logical_time": str(self._sequence),
                "source_time": source_time.isoformat() if source_time else None,
                "ingest_time": datetime.utcnow().isoformat()
            }
            
            # Write physical timestamp file
            with open(seq_file, 'w') as f:
                f.write(json.dumps(metadata, ensure_ascii=False))
            
            return self._sequence, metadata
    
    def is_stale(self, incoming_seq: int, incident_last_seq: int) -> bool:
        """
        Validate incoming observation against incident state.
        
        Stale if: incoming.logical_time <= incident.last_logical_time
        
        Args:
            incoming_seq: Logical sequence of incoming observation
            incident_last_seq: Last sequence that updated this incident
        
        Returns:
            True if observation is stale/replay
        """
        return incoming_seq <= incident_last_seq
    
    def validate_sequence_progression(
        self,
        new_seq: int,
        prev_seq: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that sequence progression is monotonic.
        
        Args:
            new_seq: New sequence value
            prev_seq: Previous sequence value (for monotonic check)
        
        Returns:
            (is_valid, error_message)
        """
        with self._lock:
            if prev_seq is not None and new_seq <= prev_seq:
                return False, f"Sequence non-monotonic: {prev_seq} -> {new_seq}"
            
            # Check against stored sequence
            stored_seq = self._load_sequence()
            if new_seq != stored_seq + 1:
                return False, f"Sequence gap: expected {stored_seq + 1}, got {new_seq}"
            
            return True, None
    
    def get_sequence_info(self, sequence: int) -> Optional[Dict[str, str]]:
        """
        Retrieve metadata for a specific sequence ID.
        
        Args:
            sequence: Sequence ID to retrieve
        
        Returns:
            Metadata dict or None if not found
        """
        seq_file = self._timestamp_dir / f"{sequence:08d}.tsv"
        if seq_file.exists():
            try:
                with open(seq_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None
    
    def get_current_sequence(self) -> int:
        """Get current sequence counter value."""
        return self._load_sequence()
    
    def reset_sequence(self) -> int:
        """Reset counter (use with extreme caution)."""
        with self._lock:
            self._sequence = 0
            self._save_sequence(0)
            return 0


def create_sequencer_service():
    """Create sequencer service with process management."""
    return IngestSequencer(
        counter_file="/home/jason2ykk/.openclaw/workspace/ingest/sequence",
        timestamp_dir="/home/jason2ykk/.openclaw/workspace/ingest/timestamps"
    )


if __name__ == "__main__":
    # Test the sequencer
    seq = create_sequencer_service()
    
    # Test sequence generation
    for i in range(5):
        seq_num, meta = seq.get_next_sequence()
        print(f"Sequence {seq_num}: {meta}")
    
    # Test staleness detection
    print("\nStaleness test:")
    print(f"Is seq 3 <= seq 5? {seq.is_stale(3, 5)}")  # Should be True
    print(f"Is seq 6 <= seq 5? {seq.is_stale(6, 5)}")  # Should be False
    
    # Test sequence progression validation
    print("\nSequence progression test:")
    valid, msg = seq.validate_sequence_progression(10, 9)
    print(f"10 after 9: {valid} - {msg}")
    
    valid, msg = seq.validate_sequence_progression(10, 10)
    print(f"10 after 10: {valid} - {msg}")  # Should be False
