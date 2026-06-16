#!/usr/bin/env python3
"""Lightweight shortcut governance status and usage log utility."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from shortcut_doctor import DEFAULT_MANIFEST, DEFAULT_REGISTRY, DEFAULT_USAGE_LOG, build_manifest, parse_shortcuts


def load_manifest(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    rows = parse_shortcuts(DEFAULT_REGISTRY)
    return build_manifest(rows)


def filter_shortcuts(manifest: dict[str, Any], group: str | None) -> list[dict[str, Any]]:
    shortcuts = list(manifest.get("shortcuts", []))
    if not group:
        return shortcuts
    return [item for item in shortcuts if item.get("group") == group]


def summarize(shortcuts: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_risk: dict[str, int] = {}
    by_group: dict[str, int] = {}
    needs_confirm = 0
    quarantined = 0
    for item in shortcuts:
        by_status[item.get("status", "unknown")] = by_status.get(item.get("status", "unknown"), 0) + 1
        by_risk[item.get("risk", "unknown")] = by_risk.get(item.get("risk", "unknown"), 0) + 1
        by_group[item.get("group", "unknown")] = by_group.get(item.get("group", "unknown"), 0) + 1
        if item.get("needs_confirm"):
            needs_confirm += 1
        if item.get("quarantined"):
            quarantined += 1
    return {
        "total": len(shortcuts),
        "by_status": by_status,
        "by_risk": by_risk,
        "by_group": by_group,
        "needs_confirm": needs_confirm,
        "quarantined": quarantined,
    }


def read_usage_tail(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def usage_summary(path: Path) -> dict[str, Any]:
    rows = read_usage_tail(path, 200)
    recent_failures: dict[str, int] = {}
    recent_uses: dict[str, int] = {}
    for row in rows:
        shortcut = str(row.get("shortcut") or "").strip()
        if not shortcut:
            continue
        recent_uses[shortcut] = recent_uses.get(shortcut, 0) + 1
        if row.get("status") == "fail":
            recent_failures[shortcut] = recent_failures.get(shortcut, 0) + 1
    return {
        "log_path": str(path),
        "recent_rows": len(rows),
        "recent_uses": recent_uses,
        "recent_failures": recent_failures,
    }


def cmd_status(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.manifest)
    shortcuts = filter_shortcuts(manifest, args.group)
    payload = {
        "schema": "openclaw.shortcut_status.v1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "group": args.group or "all",
        "summary": summarize(shortcuts),
        "usage": usage_summary(args.usage_log),
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    summary = payload["summary"]
    print(f"group={payload['group']}")
    print(f"total={summary['total']}")
    print(f"by_status={summary['by_status']}")
    print(f"by_risk={summary['by_risk']}")
    print(f"needs_confirm={summary['needs_confirm']}")
    print(f"quarantined={summary['quarantined']}")
    print(f"usage_log={payload['usage']['log_path']}")
    if payload["usage"]["recent_failures"]:
        print(f"recent_failures={payload['usage']['recent_failures']}")
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    artifacts = list(args.artifact or [])
    payload = {
        "schema": "openclaw.shortcut_usage.v1",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "shortcut": args.shortcut,
        "status": args.status,
        "summary": args.summary,
        "artifacts": artifacts,
        "next_action": args.next_action,
    }
    args.usage_log.parent.mkdir(parents=True, exist_ok=True)
    with args.usage_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"logged={args.shortcut}")
        print(f"status={args.status}")
        print(f"usage_log={args.usage_log}")
    return 0


def cmd_self_test(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "shortcut_manifest.json"
        usage = tmp_path / "shortcut_usage.jsonl"
        manifest.write_text(
            json.dumps(
                {
                    "schema": "openclaw.shortcut_manifest.v1",
                    "shortcuts": [
                        {
                            "name": "测试",
                            "group": "system",
                            "status": "已接入",
                            "risk": "read_only",
                            "needs_confirm": False,
                            "quarantined": False,
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        args = argparse.Namespace(manifest=manifest, usage_log=usage, group=None, json=True)
        assert cmd_status(args) == 0
        log_args = argparse.Namespace(
            shortcut="测试",
            status="ok",
            summary="self-test",
            artifact=[],
            next_action=None,
            usage_log=usage,
            json=True,
        )
        assert cmd_log(log_args) == 0
        assert usage.exists()
    print("PASS: shortcut status self-test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show lightweight shortcut governance status")
    status.add_argument("group", nargs="?", help="Optional group: photo, model, backup, automation, system, news, github")
    status.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    status.add_argument("--usage-log", type=Path, default=DEFAULT_USAGE_LOG)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    log = subparsers.add_parser("log", help="Append a shortcut usage contract row")
    log.add_argument("--shortcut", required=True)
    log.add_argument("--status", choices=["ok", "warn", "fail"], required=True)
    log.add_argument("--summary", required=True)
    log.add_argument("--artifact", action="append")
    log.add_argument("--next-action")
    log.add_argument("--usage-log", type=Path, default=DEFAULT_USAGE_LOG)
    log.add_argument("--json", action="store_true")
    log.set_defaults(func=cmd_log)

    self_test = subparsers.add_parser("self-test", help="Run deterministic self-test")
    self_test.set_defaults(func=cmd_self_test)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
