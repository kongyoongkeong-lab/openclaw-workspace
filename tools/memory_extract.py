#!/usr/bin/env python3
"""
Lightweight memory extractor — alternative to Mem0 integration.
Scans recent session logs / memory files for actionable facts
and appends them to memory/review/pending_review.md for confirmation.

Usage:
  python3 tools/memory_extract.py                              # scan last 24h sessions
  python3 tools/memory_extract.py --source memory/2026-05-24.md  # scan a specific file
  python3 tools/memory_extract.py --dry-run                      # preview without writing
  python3 tools/memory_extract.py --auto-approve                 # skip review, write directly
"""

import re
import json
import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/home/jason2ykk/.openclaw/workspace"))
MEMORY_DIR = WORKSPACE / "memory"
REVIEW_FILE = MEMORY_DIR / "review" / "pending_review.md"
LOG_DIR = Path("/home/jason2ykk/.openclaw/logs")
SESSION_DIR = Path("/home/jason2ykk/.openclaw/sessions")

# Patterns that indicate a memorable fact
FACT_PATTERNS = [
    (r"(?:I|Jason|user)\s+(?:prefers?|likes?|uses?)\s+(.+?)(?:\.|;|$)", "preference"),
    (r"(?:I|Jason|user)\s+wants?\s+(.+?)(?:\.|;|$)", "desire"),
    (r"(?:set|configured|changed)\s+(.+?)(?:to|as)\s+(.+?)(?:\.|;|$)", "configuration"),
    (r"don'?t\s+(?:use|run|do|install)\s+(.+?)(?:\.|;|$)", "restriction"),
    (r"(?:installed|added|enabled)\s+(.+?)(?:\.|;|$)", "installation"),
    (r"(?:decided|chose|selected)\s+(.+?)(?:\.|;|$)", "decision"),
    (r"(?:error|failed|broken|missing)\s+(.+?)(?:\.|;|$)", "issue"),
    (r"(?:remember|save|store|keep)\s+(.+?)(?:\.|;|$)", "explicit_save"),
    (r"(?:running\s+on|host|system)\s+(.+?)(?:\.|;|$)", "system_info"),
    (r"(?:GPU|VRAM|memory)\s+(is|has|at)\s+(.+?)(?:\.|;|$)", "hardware"),
]


def extract_facts(text: str, source: str = "unknown") -> list[dict]:
    """Extract candidate facts from text using pattern matching."""
    facts = []
    seen = set()

    for pattern, category in FACT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Normalize the matched text to avoid duplicates
            key = match.group(0).strip().lower()[:80]
            if key in seen:
                continue
            seen.add(key)

            facts.append({
                "category": category,
                "text": match.group(0).strip(),
                "source": source,
                "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            })

    return facts


def scan_session_logs(hours: int = 24) -> list[dict]:
    """Scan recent OpenClaw session JSONL files for assistant/user messages."""
    facts = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    if SESSION_DIR.exists():
        for session_file in SESSION_DIR.glob("**/*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    continue
                with open(session_file, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            content = entry.get("content", "") or entry.get("message", "") or str(entry)
                            if isinstance(content, str) and len(content) > 20:
                                facts.extend(extract_facts(content, str(session_file)))
                        except json.JSONDecodeError:
                            pass
            except (PermissionError, FileNotFoundError):
                pass

    return facts


def scan_log_files(hours: int = 24) -> list[dict]:
    """Scan OpenClaw log files for assistant output."""
    facts = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    if LOG_DIR.exists():
        for log_file in LOG_DIR.glob("openclaw-*.log"):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    continue
                with open(log_file, encoding="utf-8", errors="replace") as f:
                    facts.extend(extract_facts(f.read(), str(log_file)))
            except (PermissionError, FileNotFoundError):
                pass

    return facts


def scan_memory_files() -> list[dict]:
    """Scan existing memory/ files for patterns already captured."""
    facts = []
    if MEMORY_DIR.exists():
        for mfile in sorted(MEMORY_DIR.glob("*.md")):
            if "review" in str(mfile):
                continue
            try:
                with open(mfile, encoding="utf-8", errors="replace") as f:
                    facts.extend(extract_facts(f.read(), str(mfile)))
            except (PermissionError, FileNotFoundError):
                pass
    return facts


def deduplicate(facts: list[dict]) -> list[dict]:
    """Remove near-duplicate facts."""
    seen = set()
    unique = []
    for f in facts:
        key = f["text"].lower().strip()[:100]
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def format_review(facts: list[dict]) -> str:
    """Format facts as a review document."""
    if not facts:
        return "# Pending Memory Review\n\n*No new facts extracted.*\n"

    lines = [
        "# Pending Memory Review",
        f"*Generated: {datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M MYT')}*",
        f"*Total candidates: {len(facts)}*",
        "",
        "---",
        "",
    ]

    # Group by category
    categories = {}
    for f in facts:
        cat = f["category"]
        categories.setdefault(cat, []).append(f)

    for cat in sorted(categories.keys()):
        lines.append(f"## 📂 {cat}")
        lines.append("")
        for f in categories[cat]:
            lines.append(f"- [ ] `{f['timestamp'][:16]}` {f['text']}")
            lines.append(f"  *source: `{f['source']}`*")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Review instructions:*")
    lines.append("- Uncheck = skip")
    lines.append("- Check = approve for long-term memory")
    lines.append("- Edit the text directly if it needs correction")
    lines.append("- Run `python3 tools/memory_extract.py --commit` to write approved items")
    lines.append("")

    return "\n".join(lines)


def write_pending_review(content: str):
    """Write the review file, appending if it already exists."""
    REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    if REVIEW_FILE.exists():
        # Append with separator
        existing = REVIEW_FILE.read_text(encoding="utf-8")
        if existing.strip() == "*No new facts extracted.*":
            content = content.replace("*No new facts extracted.*\n", "")
        content = existing.rstrip() + "\n\n---\n\n" + content

    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Review file written: {REVIEW_FILE}")
    print(f"   {len([l for l in content.splitlines() if l.startswith('- [ ]')])} candidates pending review")


def auto_approve(facts: list[dict]) -> int:
    """Write approved facts directly to durable memory files."""
    written = 0
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    for cat, group in groupby_category(facts):
        target = MEMORY_DIR / f"extracted_{cat}.md"
        with open(target, "a", encoding="utf-8") as f:
            for fact in group:
                f.write(f"- {fact['text']}  — *{fact['source']}*\n")
                written += 1
        print(f"   → {target}: {len(list(group))} facts")

    return written


def groupby_category(facts: list[dict]) -> list[tuple[str, list[dict]]]:
    cats = {}
    for f in facts:
        cats.setdefault(f["category"], []).append(f)
    return sorted(cats.items())


def main():
    parser = argparse.ArgumentParser(description="Lightweight memory extractor")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--auto-approve", action="store_true", help="Skip review, write directly")
    parser.add_argument("--source", type=str, help="Scan a specific file instead of sessions")
    parser.add_argument("--hours", type=int, default=24, help="How far back to scan (hours)")
    args = parser.parse_args()

    if args.source:
        # Scan a single file
        path = Path(args.source)
        if not path.exists():
            print(f"❌ File not found: {path}")
            sys.exit(1)
        with open(path, encoding="utf-8", errors="replace") as f:
            facts = extract_facts(f.read(), str(path))
    else:
        # Scan sessions + logs + existing memory
        print(f"🔍 Scanning sources (last {args.hours}h)...")
        session_facts = scan_session_logs(args.hours)
        print(f"   Sessions: {len(session_facts)} candidates")
        log_facts = scan_log_files(args.hours)
        print(f"   Logs: {len(log_facts)} candidates")
        memory_facts = scan_memory_files()
        print(f"   Existing memory: {len(memory_facts)} candidates")
        facts = deduplicate(session_facts + log_facts + memory_facts)

    facts = deduplicate(facts)
    print(f"\n📊 Total unique candidates: {len(facts)}")

    if not facts:
        print("ℹ️  No new facts to extract.")
        return

    if args.dry_run:
        print("\n--- DRY RUN: Preview only ---")
        print(f"Would write: {len(facts)} candidates")
        for f in facts[:10]:
            print(f"  [{f['category']}] {f['text'][:80]}")
        if len(facts) > 10:
            print(f"  ... and {len(facts) - 10} more")
        return

    if args.auto_approve:
        written = auto_approve(facts)
        print(f"✅ Auto-approved: {written} facts written to memory/extracted_*.md")
    else:
        content = format_review(facts)
        write_pending_review(content)
        print("\n📋 Review the candidates, then run with --auto-approve to commit.")


if __name__ == "__main__":
    main()
