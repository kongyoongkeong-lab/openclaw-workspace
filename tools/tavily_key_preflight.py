#!/usr/bin/env python3
"""Check Tavily key availability without printing any key material."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "tavily_key_state.json"
TAVILY_URL = "https://api.tavily.com/search"


@dataclass(frozen=True)
class Candidate:
    label: str
    source: str
    key: str


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def add_key(candidates: list[Candidate], seen: set[str], label: str, source: str, value: str) -> None:
    key = value.strip()
    if not key or key in seen:
        return
    seen.add(key)
    candidates.append(Candidate(label=label, source=source, key=key))


def discover_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    seen: set[str] = set()
    env_file = load_env_file(Path.home() / ".openclaw" / ".env")

    sources = [("env", os.environ), ("~/.openclaw/.env", env_file)]
    for source_name, mapping in sources:
        for name, value in sorted(mapping.items()):
            if name == "TAVILY_KEYS":
                for index, item in enumerate(value.split(","), 1):
                    add_key(candidates, seen, f"TAVILY_KEYS[{index}]", source_name, item)
                continue
            if name == "TAVILY_API_KEY" or re.fullmatch(r"TAVILY_API_KEY[_A-Z0-9-]*", name):
                add_key(candidates, seen, name, source_name, value)
    return candidates


def check_key(candidate: Candidate, query: str, timeout: int) -> tuple[bool, str]:
    payload = {
        "api_key": candidate.key,
        "query": query,
        "max_results": 1,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        TAVILY_URL,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return False, f"http_{exc.code}"
    except urllib.error.URLError as exc:
        return False, f"network_error:{exc.reason}"
    except TimeoutError:
        return False, "timeout"

    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        return False, "non_json_response"

    if isinstance(obj, dict) and obj.get("results") is not None:
        return True, f"ok results={len(obj.get('results') or [])}"
    return False, "unexpected_response"


def save_state(selected: Candidate, status: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "openclaw.tavily_key_state.v1",
        "selected_label": selected.label,
        "selected_source": selected.source,
        "status": status,
        "updated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "secret_policy": "key material is never stored here",
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-all", action="store_true", help="Probe every discovered key.")
    parser.add_argument("--list-only", action="store_true", help="List discovered key labels without network probes.")
    parser.add_argument("--no-write", action="store_true", help="Do not update config/tavily_key_state.json.")
    parser.add_argument("--query", default="Tavily API health check")
    parser.add_argument("--timeout", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    candidates = discover_candidates()

    print("Tavily key preflight")
    if not candidates:
        print("No Tavily keys found in environment or ~/.openclaw/.env.")
        print("Expected key names: TAVILY_API_KEY, TAVILY_API_KEY_*, or TAVILY_KEYS.")
        print("Secret policy: token/key fields are never printed.")
        return 2

    if args.list_only:
        print("| Label | Source | Status |")
        print("|---|---|---|")
        for candidate in candidates:
            print(f"| `{candidate.label}` | `{candidate.source}` | discovered |")
        print("Mode: list-only, no network probe.")
        print("Secret policy: token/key fields are never printed.")
        return 0

    to_check = candidates if args.check_all else candidates[:1]
    selected: Candidate | None = None
    selected_status = ""

    print("| Label | Source | Status |")
    print("|---|---|---|")
    for candidate in to_check:
        ok, status = check_key(candidate, args.query, args.timeout)
        print(f"| `{candidate.label}` | `{candidate.source}` | {status} |")
        if ok and selected is None:
            selected = candidate
            selected_status = status

    if selected:
        print(f"\nSelected Tavily key label: `{selected.label}` from `{selected.source}`")
        if not args.no_write:
            save_state(selected, selected_status)
            print(f"State file: `{STATE_FILE}`")
        print("Secret policy: token/key fields are never printed.")
        return 0

    print("\nNo working Tavily key selected.")
    print("Secret policy: token/key fields are never printed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
