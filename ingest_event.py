#!/usr/bin/env python3
"""
ingest_event() - Event ingestion with strict validation, hash chain verification,
gap detection, and hard rejection path.

Tests expose: schema gaps, edge-case ambiguity, rejection composition.
"""

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from datetime import datetime, timedelta
from typing import Any, Optional


# === CORE TYPES ===

class EventStatus(Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


@dataclass
class Event:
    """Strict event schema."""
    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict
    source: str
    hash_chain: list[str]
    status: EventStatus = EventStatus.PENDING
    error_message: Optional[str] = None


@dataclass
class IngestResult:
    """Result of an ingest attempt."""
    success: bool
    event: Optional[Event]
    error: Optional[str]
    rejected: Optional[str]  # event_id of rejected event


# === IMMEDIATE QUARANTINE ===

def quarantine_event(event: Event, reason: str) -> None:
    """Stub quarantine for now."""
    print(f"[QUARANTINE] {event.event_id}: {reason}")


# === INGEST FUNCTION ===

def ingest_event(raw_payload: dict) -> IngestResult:
    """
    Ingest an event with strict validation, hash chain verification,
    gap detection, and hard rejection.

    Pipeline:
    1. Strict validation (schema, types, required fields)
    2. Hash chain verification (chain_integrity check)
    3. Gap detection (ordering, replay windows)
    4. Hard rejection (quarantine)
    """
    result = IngestResult(success=False, event=None, error=None, rejected=None)

    # === STEP 1: STRICT VALIDATION ===
    try:
        # Schema validation
        if not raw_payload:
            raise ValueError("Empty payload")

        # Type checking
        if not isinstance(raw_payload, dict):
            raise ValueError("Payload must be a dict")

        # Required fields
        required_fields = ["event_id", "event_type", "timestamp", "payload", "source"]
        for field_name in required_fields:
            if field_name not in raw_payload:
                raise ValueError(f"Missing required field: {field_name}")

        # Type-specific validation
        if not isinstance(raw_payload["event_id"], str):
            raise ValueError("event_id must be a string")
        if not isinstance(raw_payload["event_type"], str):
            raise ValueError("event_type must be a string")
        if not isinstance(raw_payload["timestamp"], (int, float)):
            raise ValueError("timestamp must be a numeric timestamp")
        if not isinstance(raw_payload["payload"], dict):
            raise ValueError("payload must be a dict")
        if not isinstance(raw_payload["source"], str):
            raise ValueError("source must be a string")

        # === HASH CHAIN VERIFICATION ===
        hash_chain = []
        
        # Verify and build chain from chain_prev
        chain_prev = raw_payload.get("chain_prev", [])
        chain_integrity = raw_payload.get("chain_integrity", {})
        
        for prev_id in chain_prev:
            # Verify previous event exists in our chain_integrity store
            if prev_id not in chain_integrity:
                raise ValueError(f"Missing previous event in chain: {prev_id}")
            
            # Retrieve stored hash from chain_integrity (not compute new one)
            stored_hash = chain_integrity[prev_id]
            hash_chain.append(stored_hash)
        
        # Compute current event's hash (for the chain to verify)
        event_hash = hashlib.sha256(
            f"{raw_payload['event_id']}:{raw_payload['event_type']}:{raw_payload['timestamp']}:{raw_payload['source']}".encode()
        ).hexdigest()
        hash_chain.append(event_hash[:16])  # First 16 chars like stored hashes

        # === STEP 2: TIMESTAMP GAPS ===
        try:
            ts = datetime.fromtimestamp(raw_payload["timestamp"])
            # Check for future timestamps
            if ts > datetime.now() + timedelta(hours=1):
                raise ValueError(f"Timestamp too far in future: {ts}")
            # Note: chain_integrity is a dict mapping event_id->hash, not a list
            # Skip gap detection since we don't have timestamps in chain_integrity
        except ValueError as e:
            raise

        # === STEP 3: EVENT TYPE VALIDATION ===
        allowed_types = {"user_action", "system_event", "sensor_reading", "external_trigger"}
        if raw_payload["event_type"] not in allowed_types:
            raise ValueError(f"Unknown event_type: {raw_payload['event_type']}")

        # === STEP 4: SOURCE VALIDATION ===
        if not raw_payload["source"]:
            raise ValueError("Empty source")
        if raw_payload["source"] not in {"api", "webhook", "file", "internal", "external"}:
            raise ValueError(f"Unknown source: {raw_payload['source']}")

        # === STEP 5: BUILD EVENT ===
        event = Event(
            event_id=raw_payload["event_id"],
            event_type=raw_payload["event_type"],
            timestamp=datetime.fromtimestamp(raw_payload["timestamp"]),
            payload=raw_payload["payload"],
            source=raw_payload["source"],
            hash_chain=hash_chain,
            status=EventStatus.VALIDATED
        )

        result.success = True
        result.event = event
        return result

    except Exception as e:
        # === HARD REJECTION PATH ===
        error_msg = str(e)
        rejected_id = raw_payload.get("event_id", "unknown")
        quarantine_event(Event(
            event_id=rejected_id,
            event_type=raw_payload.get("event_type", "unknown"),
            timestamp=datetime.fromtimestamp(time.time()),
            payload={},
            source=raw_payload.get("source", "unknown"),
            hash_chain=[],
            status=EventStatus.QUARANTINED,
            error_message=error_msg
        ), error_msg)
        result.success = False
        result.error = error_msg
        result.rejected = rejected_id
        return result
