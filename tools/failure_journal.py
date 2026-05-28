#!/usr/bin/env python3
"""Append sanitized entries to the Pentagon Failure Journal."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
ERROR_DIR = WORKSPACE / "memory" / "errors"
INDEX_PATH = ERROR_DIR / "INDEX.md"

PRIORITIES = ("low", "medium", "high", "critical")
STATUSES = ("open", "mitigated", "fixed", "watch")
AREAS = (
    "model",
    "docker",
    "n8n",
    "browser",
    "windows",
    "pdf",
    "image",
    "video",
    "memory",
    "search",
    "security",
    "docs",
    "other",
)
DETECTORS = ("user", "@main", "@intel", "@ops", "@sentinel", "tool", "test")

ERR_ID_RE = re.compile(r"\bERR-(\d{8})-(\d{3})\b")
INDEX_ROW_RE = re.compile(r"^\| (?P<rule>.+?) \| `(?P<source>ERR-\d{8}-\d{3})` \| (?P<status>.+?) \|$")

SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|rk|pk|xox[baprs]|gh[pousr]|glpat|hf|tvly|tavily)[_-][A-Za-z0-9][A-Za-z0-9._-]{16,}\b", re.I),
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?cookie|jwt|password|passwd|secret)\b\s*[:=]\s*['\"]?[^'\"\s]{8,}", re.I),
    re.compile(r"\bn8n-auth=[A-Za-z0-9._~+/=-]{16,}", re.I),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.I),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


@dataclass(frozen=True)
class Entry:
    error_id: str
    date: dt.date
    title: str
    priority: str
    status: str
    area: str
    detected_by: str
    summary: str
    command: str
    input_class: str
    environment: str
    error_signal: str
    root_cause: str
    recovery: str
    prevention_rule: str
    files: str
    services: str
    see_also: str


def today() -> dt.date:
    return dt.date.today()


def parse_date(value: str | None) -> dt.date:
    if not value:
        return today()
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid --date {value!r}; expected YYYY-MM-DD") from exc


def month_path(date_value: dt.date) -> Path:
    return ERROR_DIR / f"{date_value:%Y-%m}.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def all_existing_ids() -> list[tuple[str, int]]:
    ids: list[tuple[str, int]] = []
    for path in ERROR_DIR.glob("*.md"):
        if path.name in {"README.md", "TEMPLATE.md", "INDEX.md"}:
            continue
        for match in ERR_ID_RE.finditer(read_text(path)):
            ids.append((match.group(1), int(match.group(2))))
    return ids


def next_error_id(date_value: dt.date) -> str:
    date_key = date_value.strftime("%Y%m%d")
    same_day_numbers = [number for found_date, number in all_existing_ids() if found_date == date_key]
    return f"ERR-{date_key}-{max(same_day_numbers, default=0) + 1:03d}"


def normalize_multiline(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.strip().splitlines()).strip()


def validate_no_secrets(fields: dict[str, str]) -> None:
    hits: list[str] = []
    for name, value in fields.items():
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                hits.append(name)
                break
    if hits:
        unique_hits = ", ".join(sorted(set(hits)))
        raise SystemExit(f"Refusing to write possible secret material in: {unique_hits}")


def markdown_bullets(csv_value: str) -> str:
    parts = [part.strip() for part in csv_value.split(",") if part.strip()]
    if not parts:
        return "- none"
    return "\n".join(f"- {part}" for part in parts)


def render_entry(entry: Entry) -> str:
    return f"""## {entry.error_id} — {entry.title}

**Date:** {entry.date.isoformat()}
**Priority:** {entry.priority}
**Status:** {entry.status}
**Area:** {entry.area}
**Detected By:** {entry.detected_by}

### Summary
{entry.summary}

### Trigger
- Command/workflow: {entry.command}
- Input class: {entry.input_class}
- Environment: {entry.environment}

### Error Signal
{entry.error_signal}

### Root Cause
{entry.root_cause}

### Recovery
{entry.recovery}

### Prevention Rule
{entry.prevention_rule}

### Related
- Files:
{markdown_bullets(entry.files)}
- Services:
{markdown_bullets(entry.services)}
- See also:
{markdown_bullets(entry.see_also)}
"""


def append_to_monthly_log(entry: Entry, dry_run: bool) -> Path:
    path = month_path(entry.date)
    if dry_run:
        return path

    ERROR_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# Failure Journal — {entry.date:%Y-%m}\n\n", encoding="utf-8")

    existing = path.read_text(encoding="utf-8")
    separator = "\n---\n\n" if "## ERR-" in existing else ""
    with path.open("a", encoding="utf-8") as handle:
        if not existing.endswith("\n"):
            handle.write("\n")
        handle.write(separator)
        handle.write(render_entry(entry).rstrip() + "\n")
    return path


def update_index(entry: Entry, dry_run: bool) -> bool:
    if dry_run:
        return False
    if not INDEX_PATH.exists():
        INDEX_PATH.write_text(
            "# Failure Journal Index\n\n"
            f"Last updated: {entry.date.isoformat()}\n\n"
            "## Active Prevention Rules\n\n"
            "| Rule | Source | Status |\n"
            "|---|---|---|\n\n"
            "## Monthly Logs\n\n",
            encoding="utf-8",
        )

    text = INDEX_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        match = INDEX_ROW_RE.match(line)
        if match and match.group("rule") == entry.prevention_rule:
            return False

    new_row = f"| {entry.prevention_rule} | `{entry.error_id}` | {entry.status} |"
    if "|---|---|---|" not in text:
        raise SystemExit(f"Cannot update malformed index: {INDEX_PATH}")

    lines = text.splitlines()
    separator_idx = lines.index("|---|---|---|")
    insert_at = separator_idx + 1
    while insert_at < len(lines) and lines[insert_at].startswith("| "):
        insert_at += 1
    updated = lines[:insert_at] + [new_row] + lines[insert_at:]

    monthly_name = f"{entry.date:%Y-%m}.md"
    monthly_line = f"- `{monthly_name}`"
    if monthly_line not in updated:
        try:
            monthly_idx = updated.index("## Monthly Logs")
            insert_at = monthly_idx + 1
            while insert_at < len(updated) and updated[insert_at].strip() == "":
                insert_at += 1
            updated.insert(insert_at, monthly_line)
        except ValueError:
            updated.extend(["", "## Monthly Logs", "", monthly_line])

    content = "\n".join(updated) + "\n"
    content = re.sub(r"Last updated: \d{4}-\d{2}-\d{2}", f"Last updated: {entry.date.isoformat()}", content)
    INDEX_PATH.write_text(content, encoding="utf-8")
    return True


def build_entry(args: argparse.Namespace) -> Entry:
    date_value = parse_date(args.date)
    error_id = args.id or next_error_id(date_value)
    fields = {
        "title": args.title,
        "summary": args.summary,
        "command": args.command,
        "input_class": args.input_class,
        "environment": args.environment,
        "error_signal": args.error_signal,
        "root_cause": args.root_cause,
        "recovery": args.recovery,
        "prevention_rule": args.prevention_rule,
        "files": args.files,
        "services": args.services,
        "see_also": args.see_also,
    }
    fields = {key: normalize_multiline(value) for key, value in fields.items()}
    validate_no_secrets(fields)

    return Entry(
        error_id=error_id,
        date=date_value,
        title=fields["title"],
        priority=args.priority,
        status=args.status,
        area=args.area,
        detected_by=args.detected_by,
        summary=fields["summary"],
        command=fields["command"],
        input_class=fields["input_class"],
        environment=fields["environment"],
        error_signal=fields["error_signal"],
        root_cause=fields["root_cause"],
        recovery=fields["recovery"],
        prevention_rule=fields["prevention_rule"],
        files=fields["files"],
        services=fields["services"],
        see_also=fields["see_also"],
    )


def command_next_id(args: argparse.Namespace) -> int:
    print(next_error_id(parse_date(args.date)))
    return 0


def command_scan(args: argparse.Namespace) -> int:
    paths = [ERROR_DIR / "README.md", ERROR_DIR / "TEMPLATE.md", INDEX_PATH]
    paths.extend(path for path in ERROR_DIR.glob("20*.md"))
    findings: list[str] = []
    for path in sorted(set(paths)):
        text = read_text(path)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(WORKSPACE)))
                break
    if findings:
        print("Possible secret material found:")
        for finding in findings:
            print(f"- {finding}")
        return 2
    print("No secret-like material found in failure journal files.")
    return 0


def command_add(args: argparse.Namespace) -> int:
    entry = build_entry(args)
    path = append_to_monthly_log(entry, args.dry_run)
    index_updated = update_index(entry, args.dry_run)
    result = {
        "id": entry.error_id,
        "monthly_log": str(path.relative_to(WORKSPACE)),
        "index_updated": index_updated,
        "dry_run": args.dry_run,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        action = "would add" if args.dry_run else "added"
        print(f"{action} {entry.error_id} -> {result['monthly_log']}")
        if not args.dry_run:
            print(f"index_updated={str(index_updated).lower()}")
    if args.dry_run:
        print()
        print(render_entry(entry).rstrip())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage memory/errors failure journal entries.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    next_id = subparsers.add_parser("next-id", help="Print the next error ID for a date.")
    next_id.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")
    next_id.set_defaults(func=command_next_id)

    scan = subparsers.add_parser("scan", help="Scan failure journal files for secret-like material.")
    scan.set_defaults(func=command_scan)

    add = subparsers.add_parser("add", help="Append a new sanitized failure entry.")
    add.add_argument("--id", help="Explicit ID. Defaults to next ERR-YYYYMMDD-NNN for --date.")
    add.add_argument("--date", help="Date in YYYY-MM-DD format. Defaults to today.")
    add.add_argument("--title", required=True)
    add.add_argument("--priority", choices=PRIORITIES, default="medium")
    add.add_argument("--status", choices=STATUSES, default="open")
    add.add_argument("--area", choices=AREAS, default="other")
    add.add_argument("--detected-by", choices=DETECTORS, default="@main")
    add.add_argument("--summary", required=True)
    add.add_argument("--command", default="none")
    add.add_argument("--input-class", default="none")
    add.add_argument("--environment", default="local workspace")
    add.add_argument("--error-signal", required=True)
    add.add_argument("--root-cause", required=True)
    add.add_argument("--recovery", required=True)
    add.add_argument("--prevention-rule", required=True)
    add.add_argument("--files", default="none", help="Comma-separated related files.")
    add.add_argument("--services", default="none", help="Comma-separated related services.")
    add.add_argument("--see-also", default="none", help="Comma-separated related IDs/docs.")
    add.add_argument("--dry-run", action="store_true")
    add.add_argument("--json", action="store_true", help="Emit machine-readable result.")
    add.set_defaults(func=command_add)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
