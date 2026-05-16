"""Replay Kernel v0 deterministic replay and snapshot helpers."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Iterable, Sequence

from .reducer import apply_event, initial_state
from .schema import Event


def canonical_json(value: Any) -> str:
    """Stable JSON representation used for deterministic hashes."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def state_hash(state: dict[str, Any]) -> str:
    """SHA256 over canonical state JSON."""
    return hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


def replay(events: Sequence[Event], seed_state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Replay events in list order."""
    state = deepcopy(seed_state) if seed_state is not None else initial_state()
    for event in events:
        state = apply_event(state, event)
    return state


def make_snapshot(events: Sequence[Event], state_id: str = "snapshot_v0") -> dict[str, Any]:
    """Build a deterministic snapshot from a prefix event log."""
    state = replay(events)
    last_event_id = events[-1].event_id if events else None
    return {
        "version": "replay_kernel_v0.snapshot.v1",
        "state_id": state_id,
        "last_event_id": last_event_id,
        "state_hash": state_hash(state),
        "state": state,
    }


def restore_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a deep copy of snapshot state."""
    state = deepcopy(snapshot["state"])
    expected_hash = snapshot["state_hash"]
    actual_hash = state_hash(state)
    if actual_hash != expected_hash:
        raise ValueError("snapshot state_hash mismatch")
    return state


def replay_from_snapshot(snapshot: dict[str, Any], tail_events: Iterable[Event]) -> dict[str, Any]:
    """Replay tail events from a validated snapshot state."""
    return replay(list(tail_events), seed_state=restore_snapshot(snapshot))
