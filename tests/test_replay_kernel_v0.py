"""Deterministic CI tests for Replay Kernel v0."""

from __future__ import annotations

import json
from pathlib import Path

from replay_kernel_v0 import Event, make_snapshot, replay, replay_from_snapshot, state_hash

FIXTURE_EVENTS = [
    Event("evt_001", "2026-05-16T00:00:00Z", "system", {"phase": "H1", "mode": "strict"}),
    Event("evt_002", "2026-05-16T00:01:00Z", "user_message", {"content": "hello", "metadata": {"channel": "webchat"}}),
    Event("evt_003", "2026-05-16T00:02:00Z", "assistant_message", {"content": "Stable. No user action required."}),
    Event("evt_004", "2026-05-16T00:03:00Z", "decision", {"content": "preserve-runtime-invariants"}),
]

SNAPSHOT_FIXTURE = Path("snapshots/replay_kernel_v0_prefix_snapshot.json")


def test_replay_log_equals_replay_log() -> None:
    assert replay(FIXTURE_EVENTS) == replay(FIXTURE_EVENTS)


def test_replay_hash_is_deterministic() -> None:
    first = state_hash(replay(FIXTURE_EVENTS))
    second = state_hash(replay(FIXTURE_EVENTS))
    assert first == second


def test_replay_fails_on_nondeterministic_output_shape() -> None:
    expected = replay(FIXTURE_EVENTS)
    mutated = replay(FIXTURE_EVENTS)
    mutated["system"]["nondeterministic"] = "forbidden"
    assert mutated != expected
    assert state_hash(mutated) != state_hash(expected)


def test_snapshot_compatibility_fixture_loads() -> None:
    snapshot = json.loads(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
    restored = snapshot["state"]
    assert snapshot["version"] == "replay_kernel_v0.snapshot.v1"
    assert snapshot["state_hash"] == state_hash(restored)


def test_replay_snapshot_plus_tail_equals_live_state() -> None:
    prefix = FIXTURE_EVENTS[:2]
    tail = FIXTURE_EVENTS[2:]
    snapshot = make_snapshot(prefix, state_id="ci_prefix")
    assert replay_from_snapshot(snapshot, tail) == replay(FIXTURE_EVENTS)


def test_committed_snapshot_plus_tail_equals_live_state() -> None:
    snapshot = json.loads(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))
    tail = FIXTURE_EVENTS[2:]
    assert replay_from_snapshot(snapshot, tail) == replay(FIXTURE_EVENTS)


def test_replay_ordering_is_preserved() -> None:
    ordered = replay(FIXTURE_EVENTS)
    reversed_state = replay(list(reversed(FIXTURE_EVENTS)))
    assert ordered != reversed_state


def test_reducer_does_not_mutate_input_state() -> None:
    seed = {"messages": [], "decisions": [], "system": {"phase": "H1"}}
    before = json.loads(json.dumps(seed))
    replay([FIXTURE_EVENTS[1]], seed_state=seed)
    assert seed == before
