#!/usr/bin/env python3
"""Safe OpenAI-Codex quota/profile snapshot for the `额度查询` shortcut.

This script intentionally prints only account labels and quota/status metadata.
It never prints OAuth access tokens, refresh tokens, gateway tokens, or API keys.
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
AUTH_STATE_FILE = OPENCLAW_DIR / "agents" / "main" / "agent" / "auth-state.json"
PROVIDER = "openai-codex"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fmt_time(ms: int | None) -> str:
    if not ms:
        return "-"
    return datetime.fromtimestamp(ms / 1000).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def is_blocked(stats: dict[str, Any], now_ms: int) -> str:
    blocked_until = stats.get("blockedUntil")
    if isinstance(blocked_until, int) and blocked_until > now_ms:
        reason = stats.get("blockedReason") or "blocked"
        return f"{reason} until {fmt_time(blocked_until)}"
    reason = stats.get("blockedReason")
    if reason:
        return f"previous {reason}"
    return "ok"


def get_profiles(config: dict[str, Any]) -> list[dict[str, str]]:
    profiles = config.get("auth", {}).get("profiles", {})
    rows: list[dict[str, str]] = []
    for profile_id, profile in sorted(profiles.items()):
        if profile.get("provider") != PROVIDER and not profile_id.startswith(f"{PROVIDER}:"):
            continue
        rows.append(
            {
                "profile": profile_id,
                "email": profile.get("email") or profile_id.removeprefix(f"{PROVIDER}:"),
                "mode": profile.get("mode") or profile.get("type") or "unknown",
            }
        )
    return rows


def get_usage(timeout: int) -> dict[str, Any] | None:
    if not shutil.which("openclaw"):
        return None
    try:
        result = subprocess.run(
            ["openclaw", "status", "--usage", "--json"],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    for provider in payload.get("usage", {}).get("providers", []):
        if provider.get("provider") == PROVIDER:
            return provider
    return None


def print_profiles(rows: list[dict[str, str]], auth_state: dict[str, Any]) -> None:
    now_ms = int(time.time() * 1000)
    last_good = auth_state.get("lastGood", {}).get(PROVIDER)
    usage_stats = auth_state.get("usageStats", {})

    print("OpenAI-Codex profiles")
    print("| Profile | Email | Mode | Runtime state |")
    print("|---|---|---|---|")
    for row in rows:
        profile_id = row["profile"]
        marker = "active" if profile_id == last_good else is_blocked(usage_stats.get(profile_id, {}), now_ms)
        print(f"| `{profile_id}` | `{row['email']}` | `{row['mode']}` | {marker} |")


def print_usage(usage: dict[str, Any] | None) -> None:
    print("\nCurrent visible quota")
    if not usage:
        print("Live quota unavailable from `openclaw status --usage`; profile list above is still valid.")
        return

    plan = usage.get("plan") or "-"
    print(f"Provider: `{usage.get('provider', PROVIDER)}`")
    print(f"Plan: `{plan}`")
    print("| Window | Left | Used | Reset |")
    print("|---|---:|---:|---|")
    for window in usage.get("windows", []):
        used = int(window.get("usedPercent", 0))
        left = max(100 - used, 0)
        print(f"| {window.get('label', '-')} | {left}% | {used}% | {fmt_time(window.get('resetAt'))} |")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-only", action="store_true", help="Dry-run mode: do not call live OpenClaw usage probe.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic parser/redaction self-test.")
    parser.add_argument("--timeout", type=int, default=25, help="Seconds to wait for `openclaw status --usage`.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        sample = {"usageStats": {f"{PROVIDER}:demo@example.com": {"blockedReason": "rate_limit"}}}
        assert is_blocked(sample["usageStats"][f"{PROVIDER}:demo@example.com"], int(time.time() * 1000)) == "previous rate_limit"
        print("PASS: quota query self-test passed.")
        return 0
    config = load_json(CONFIG_FILE)
    auth_state = load_json(AUTH_STATE_FILE)
    profiles = get_profiles(config)
    if not profiles:
        raise SystemExit(f"No {PROVIDER} auth profiles found in {CONFIG_FILE}")

    print_profiles(profiles, auth_state)
    if not args.profiles_only:
        print_usage(get_usage(args.timeout))
    print("\nSecret policy: token/key fields are never printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
