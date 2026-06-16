#!/usr/bin/env python3
"""Workspace-local pending action cache for short confirmation replies."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_FILE = ROOT / "config" / "pending_action.json"
SCHEMA = "openclaw.pending_action.v1"
DEFAULT_TTL_MINUTES = 45


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def base_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "pending": None,
        "updated_at": now_iso(),
        "notes": [
            "Stores the last user-visible action that can be approved by short replies such as confirm proceed.",
            "Do not store secrets, tokens, API keys, browser cookies, or full private file contents.",
        ],
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return base_state()
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema") != SCHEMA:
        raise SystemExit(f"Unsupported pending action schema in {path}")
    state.setdefault("pending", None)
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = now_iso()
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_expired(pending: dict[str, Any], now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc).astimezone()
    expires_at = parse_time(pending.get("expires_at"))
    return bool(expires_at and now > expires_at)


def public_pending(pending: dict[str, Any] | None) -> dict[str, Any] | None:
    if not pending:
        return None
    allowed = {
        "id",
        "title",
        "summary",
        "risk",
        "requires_confirmation",
        "created_at",
        "expires_at",
        "created_by",
        "status",
    }
    return {key: value for key, value in pending.items() if key in allowed}


def cmd_get(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    pending = state.get("pending")
    if pending and is_expired(pending):
        pending["status"] = "expired"
        save_state(args.state_file, state)
    if args.json:
        print(json.dumps({"pending": public_pending(state.get("pending"))}, indent=2, ensure_ascii=False))
    elif not state.get("pending"):
        print("pending_action=none")
    else:
        item = state["pending"]
        print(f"pending_action={item.get('id')}")
        print(f"title={item.get('title')}")
        print(f"status={item.get('status', 'pending')}")
        print(f"risk={item.get('risk', 'unknown')}")
        print(f"expires_at={item.get('expires_at', 'unknown')}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    created_at = now_iso()
    expires_at = (
        datetime.now(timezone.utc).astimezone() + timedelta(minutes=args.ttl_minutes)
    ).isoformat(timespec="seconds")
    state["pending"] = {
        "id": args.action_id,
        "title": args.title,
        "summary": args.summary,
        "risk": args.risk,
        "requires_confirmation": True,
        "created_at": created_at,
        "expires_at": expires_at,
        "created_by": args.source,
        "status": "pending",
    }
    save_state(args.state_file, state)
    print(f"pending_action={args.action_id}")
    print(f"state_file={args.state_file}")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    cmd_set(args)
    print("confirmation_prompt=Reply `confirm proceed` to approve this pending action.")
    print("safety=Pending action metadata is local and must not contain secrets.")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    state["pending"] = None
    save_state(args.state_file, state)
    print("pending_action=none")
    return 0


def cmd_consume(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    pending = state.get("pending")
    if not pending:
        print("pending_action=none")
        print(f"decision=none")
        print(f"source={args.source}")
        return 0
    if is_expired(pending):
        pending["status"] = "expired"
        save_state(args.state_file, state)
        print(f"pending_action_expired={pending.get('id')}")
        print("decision=expired")
        print(f"source={args.source}")
        return 0
    action_id = pending.get("id", "unknown")
    if args.mark == "approved":
        state["pending"] = None
    else:
        pending["status"] = args.mark
    save_state(args.state_file, state)
    print(f"pending_action={action_id}")
    print(f"decision={args.mark}")
    print(f"source={args.source}")
    return 0


def cmd_self_test(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        state_file = Path(tmp) / "pending_action.json"
        set_args = argparse.Namespace(
            state_file=state_file,
            action_id="T-SELFTEST",
            title="Self-test pending action",
            summary="No external side effects",
            risk="low",
            source="self-test",
            ttl_minutes=DEFAULT_TTL_MINUTES,
        )
        cmd_set(set_args)
        state = load_state(state_file)
        assert state["pending"]["id"] == "T-SELFTEST"
        consume_args = argparse.Namespace(
            state_file=state_file,
            mark="approved",
            source="self-test",
        )
        assert cmd_consume(consume_args) == 0
        assert load_state(state_file)["pending"] is None
        assert cmd_consume(consume_args) == 0
        ask_args = argparse.Namespace(
            state_file=state_file,
            action_id="T-ASK",
            title="Self-test confirmation ask",
            summary="Stores a confirmation prompt",
            risk="low",
            source="self-test",
            ttl_minutes=DEFAULT_TTL_MINUTES,
        )
        assert cmd_ask(ask_args) == 0
        assert load_state(state_file)["pending"]["id"] == "T-ASK"
    print("PASS: pending action self-test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    subparsers = parser.add_subparsers(dest="command", required=True)

    get_parser = subparsers.add_parser("get", help="Show the current pending action")
    get_parser.add_argument("--json", action="store_true")
    get_parser.set_defaults(func=cmd_get)

    set_parser = subparsers.add_parser("set", help="Store a pending action")
    set_parser.add_argument("--id", dest="action_id", required=True)
    set_parser.add_argument("--title", required=True)
    set_parser.add_argument("--summary", required=True)
    set_parser.add_argument("--risk", choices=["low", "medium", "high"], default="medium")
    set_parser.add_argument("--source", default="manual")
    set_parser.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES)
    set_parser.set_defaults(func=cmd_set)

    ask_parser = subparsers.add_parser("ask", help="Store a pending action and print a confirm-proceed prompt")
    ask_parser.add_argument("--id", dest="action_id", required=True)
    ask_parser.add_argument("--title", required=True)
    ask_parser.add_argument("--summary", required=True)
    ask_parser.add_argument("--risk", choices=["low", "medium", "high"], default="medium")
    ask_parser.add_argument("--source", default="manual")
    ask_parser.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES)
    ask_parser.set_defaults(func=cmd_ask)

    clear_parser = subparsers.add_parser("clear", help="Clear the pending action")
    clear_parser.set_defaults(func=cmd_clear)

    consume_parser = subparsers.add_parser("consume", help="Record a confirmation decision")
    consume_parser.add_argument("--mark", choices=["approved", "rejected"], default="approved")
    consume_parser.add_argument("--source", default="manual")
    consume_parser.set_defaults(func=cmd_consume)

    self_test_parser = subparsers.add_parser("self-test", help="Run deterministic self-test")
    self_test_parser.set_defaults(func=cmd_self_test)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
