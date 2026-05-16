# Replay Kernel v0

Minimal deterministic replay primitives for OpenClaw engineering validation.

## Architecture Overview

Replay Kernel v0 is intentionally small:

- `schema.py` defines immutable event records.
- `reducer.py` applies one event to a state copy.
- `replay.py` replays ordered logs and validates snapshots.
- `tests/test_replay_kernel_v0.py` enforces deterministic invariants.
- `snapshots/` stores compatibility fixtures.

No runtime self-modification, external retrieval, network calls, cache layers, or governance layers are part of this workflow.

## Replay Flow

```text
event log -> replay(events) -> state -> canonical hash
```

Core invariant:

```python
replay(log) == replay(log)
```

Event order is preserved. Reordering events must produce a different state when the ordered semantics differ.

## Snapshot Strategy

Snapshots are compatibility fixtures, not live runtime checkpoints.

```text
prefix log -> snapshot(state) + tail events -> restored state
full log ----------------------------------> live state
```

Core invariant:

```python
replay(snapshot + tail) == live_state
```

Each snapshot includes:

- `version`
- `state_id`
- `last_event_id`
- `state_hash`
- `state`

`state_hash` is SHA256 over canonical JSON.

## Invariant Guarantees

CI enforces:

1. Unit tests pass.
2. Replay output is deterministic across repeated runs.
3. Snapshot fixtures remain compatible.
4. Nondeterministic state changes fail tests.
5. Replay primitives do not use runtime write surfaces.

## Branch Policy

- Human-reviewed PRs only.
- No direct push to `main`.
- No autonomous merges.
- No agent-driven commits to `main`.
- Runtime behavior changes require explicit human approval.

## Freeze Policy

Do not modify reducer logic, event schema semantics, or replay ordering behavior unless a human-reviewed PR explicitly authorizes a new version.
