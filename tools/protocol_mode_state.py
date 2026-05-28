#!/usr/bin/env python3
"""Manage workspace-local OpenClaw protocol mode."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "protocol_mode.json"
VALID_MODES = {"stable", "architect_mode"}
DEFAULT_STATE = {
    "schema": "openclaw.protocol_mode.v1",
    "default_mode": "stable",
    "active_mode": "stable",
    "updated_at": None,
    "updated_by": "default",
    "safety_invariants": [
        "production activation requires explicit approval",
        "new agents require explicit approval",
        "telemetry expansion requires explicit approval",
        "Qdrant writes require explicit approval",
        "workflow changes require explicit approval",
        "persistent background tasks require explicit approval",
    ],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_state() -> dict:
    if not STATE_FILE.exists():
        return dict(DEFAULT_STATE)
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    merged = dict(DEFAULT_STATE)
    merged.update(state)
    return merged


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cmd_get(_: argparse.Namespace) -> int:
    state = load_state()
    print(f"active_mode={state.get('active_mode', 'stable')}")
    print(f"default_mode={state.get('default_mode', 'stable')}")
    print(f"updated_at={state.get('updated_at') or 'never'}")
    print(f"updated_by={state.get('updated_by', 'unknown')}")
    for invariant in state.get("safety_invariants", []):
        print(f"safety_invariant={invariant}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    state = load_state()
    state["active_mode"] = args.mode
    state["updated_at"] = now_iso()
    state["updated_by"] = args.source
    save_state(state)
    print(f"active_mode={args.mode}")
    print(f"state_file={STATE_FILE}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get", help="Show active protocol mode")
    get_parser.set_defaults(func=cmd_get)

    set_parser = subparsers.add_parser("set", help="Set active protocol mode")
    set_parser.add_argument("mode", choices=sorted(VALID_MODES))
    set_parser.add_argument("--source", default="manual")
    set_parser.set_defaults(func=cmd_set)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
