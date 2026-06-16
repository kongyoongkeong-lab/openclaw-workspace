#!/usr/bin/env python3
"""Choose the best OpenAI-Codex auth profile order without printing secrets.

Default behavior writes per-agent auth order overrides for existing OpenClaw
agent state directories. Use --dry-run to inspect only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

OPENCLAW_DIR = Path.home() / ".openclaw"
CONFIG_FILE = OPENCLAW_DIR / "openclaw.json"
MAIN_AGENT_DIR = OPENCLAW_DIR / "agents" / "main" / "agent"
AUTH_STATE_FILE = MAIN_AGENT_DIR / "auth-state.json"
PROVIDER = "openai-codex"
DEFAULT_AGENTS = ["main", "intel", "ops", "sentinel"]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fmt_time(ms: int | None) -> str:
    if not ms:
        return "-"
    return datetime.fromtimestamp(ms / 1000).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def codex_profiles(config: dict[str, Any]) -> list[dict[str, str]]:
    profiles = config.get("auth", {}).get("profiles", {})
    rows: list[dict[str, str]] = []
    for profile_id, profile in profiles.items():
        if profile.get("provider") == PROVIDER or profile_id.startswith(f"{PROVIDER}:"):
            rows.append(
                {
                    "profile": profile_id,
                    "email": profile.get("email") or profile_id.removeprefix(f"{PROVIDER}:"),
                    "mode": profile.get("mode") or profile.get("type") or "unknown",
                }
            )
    return sorted(rows, key=lambda item: item["profile"])


def profile_state(profile_id: str, auth_state: dict[str, Any], now_ms: int) -> tuple[int, str]:
    stats = auth_state.get("usageStats", {}).get(profile_id, {})
    blocked_until = stats.get("blockedUntil")
    blocked_reason = stats.get("blockedReason")
    if isinstance(blocked_until, int) and blocked_until > now_ms:
        return (2, f"{blocked_reason or 'blocked'} until {fmt_time(blocked_until)}")
    if blocked_reason:
        return (1, f"previous {blocked_reason}")
    return (0, "ok")


def ordered_profiles(rows: list[dict[str, str]], auth_state: dict[str, Any]) -> list[dict[str, str]]:
    now_ms = int(time.time() * 1000)
    last_good = auth_state.get("lastGood", {}).get(PROVIDER)

    def sort_key(row: dict[str, str]) -> tuple[int, int, str]:
        blocked_rank, _ = profile_state(row["profile"], auth_state, now_ms)
        active_rank = 0 if row["profile"] == last_good else 1
        return (blocked_rank, active_rank, row["profile"])

    ordered = []
    for row in sorted(rows, key=sort_key):
        _, state = profile_state(row["profile"], auth_state, now_ms)
        enriched = dict(row)
        enriched["state"] = "active" if row["profile"] == last_good and state == "ok" else state
        ordered.append(enriched)
    return ordered


def agent_dir(agent: str) -> Path:
    return OPENCLAW_DIR / "agents" / agent / "agent"


def set_order_with_cli(agent: str, provider: str, order: list[str], timeout: int) -> tuple[bool, str]:
    if not shutil.which("openclaw"):
        return False, "openclaw CLI missing"
    cmd = ["openclaw", "models", "auth", "order", "set", "--agent", agent, "--provider", provider, *order]
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    return result.returncode == 0, output or "ok"


def set_order_direct(agent: str, provider: str, order: list[str]) -> None:
    path = agent_dir(agent) / "auth-state.json"
    state = load_json(path)
    state.setdefault("version", 1)
    state.setdefault("order", {})
    state["order"][provider] = order
    write_json(path, state)


def print_table(rows: list[dict[str, str]]) -> None:
    print("OpenAI-Codex quota preflight")
    print("| Rank | Profile | Email | Mode | State |")
    print("|---:|---|---|---|---|")
    for index, row in enumerate(rows, 1):
        print(f"| {index} | `{row['profile']}` | `{row['email']}` | `{row['mode']}` | {row['state']} |")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Show selected order without writing auth-state.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic ordering self-test.")
    parser.add_argument("--provider", default=PROVIDER)
    parser.add_argument("--agents", nargs="+", default=DEFAULT_AGENTS)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Write auth-state.json directly instead of using `openclaw models auth order set`.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        rows = [
            {"profile": "openai-codex:a@example.com", "email": "a@example.com", "mode": "plus", "state": "blocked until tomorrow"},
            {"profile": "openai-codex:b@example.com", "email": "b@example.com", "mode": "plus", "state": "ok"},
        ]
        ordered = ordered_profiles(rows, {"usageStats": {"openai-codex:a@example.com": {"blockedUntil": 4102444800000}}})
        assert ordered[0]["profile"] == "openai-codex:b@example.com"
        print("PASS: codex quota preflight self-test passed.")
        return 0
    config = load_json(CONFIG_FILE)
    auth_state = load_json(AUTH_STATE_FILE)
    rows = codex_profiles(config)
    if not rows:
        raise SystemExit(f"No {args.provider} profiles found in {CONFIG_FILE}")

    ordered = ordered_profiles(rows, auth_state)
    order = [row["profile"] for row in ordered]
    print_table(ordered)
    print(f"\nSelected order: {', '.join(order)}")

    existing_agents = [agent for agent in args.agents if agent_dir(agent).exists()]
    missing_agents = [agent for agent in args.agents if not agent_dir(agent).exists()]

    if args.dry_run:
        print("Mode: dry-run, no files changed.")
    else:
        for agent in existing_agents:
            if args.direct:
                set_order_direct(agent, args.provider, order)
                print(f"Applied: {agent} via direct auth-state update")
                continue
            ok, output = set_order_with_cli(agent, args.provider, order, args.timeout)
            if not ok:
                raise SystemExit(f"Failed to apply order for {agent}: {output}")
            print(f"Applied: {agent}")

    if missing_agents:
        print(f"Skipped missing agent state dirs: {', '.join(missing_agents)}")
    print("Secret policy: token/key fields are never printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
