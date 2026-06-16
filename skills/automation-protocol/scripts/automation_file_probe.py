#!/usr/bin/env python3
"""Find likely Windows/WSL files and verify automation outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SEARCH_ROOTS = [
    Path("/mnt/c/Users/jason/Desktop"),
    Path("/mnt/c/Users/jason/OneDrive/Desktop"),
    Path("/mnt/c/Users/jason/Documents"),
    Path("/mnt/d/_inbox"),
    Path("/mnt/d/_outbox"),
]


def stat_payload(path: Path) -> dict:
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": st.st_size,
        "mtime": st.st_mtime,
        "suffix": path.suffix,
    }


def find(name: str) -> list[dict]:
    matches: list[Path] = []
    candidate = Path(name)
    if candidate.exists():
        matches.append(candidate)
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        direct = root / name
        if direct.exists():
            matches.append(direct)
        matches.extend(root.glob(name))
    unique = {p.resolve(): p for p in matches}
    return [stat_payload(p) for p in sorted(unique.values(), key=lambda p: p.stat().st_mtime, reverse=True)]


def verify(path: str, suffix: str | None = None) -> dict:
    p = Path(path)
    if not p.exists():
        return {"path": str(p), "exists": False, "ok": False, "reason": "missing"}
    payload = stat_payload(p)
    ok = payload["size"] > 0
    if suffix and p.suffix.lower() != suffix.lower():
        ok = False
        payload["reason"] = f"expected suffix {suffix}, got {p.suffix}"
    payload["ok"] = ok
    if not ok and "reason" not in payload:
        payload["reason"] = "empty file"
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_find = sub.add_parser("find")
    p_find.add_argument("name")
    p_verify = sub.add_parser("verify")
    p_verify.add_argument("path")
    p_verify.add_argument("--suffix")
    sub.add_parser("self-test")
    args = parser.parse_args()

    if args.cmd == "find":
        print(json.dumps(find(args.name), indent=2, ensure_ascii=False))
    elif args.cmd == "verify":
        print(json.dumps(verify(args.path, args.suffix), indent=2, ensure_ascii=False))
    else:
        payload = stat_payload(Path(__file__))
        assert payload["exists"] and payload["size"] > 0
        print("PASS: automation file probe self-test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
