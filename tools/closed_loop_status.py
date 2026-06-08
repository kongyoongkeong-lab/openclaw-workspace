#!/usr/bin/env python3
"""Read-only closed-loop status report for OpenClaw improvement work."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTBOX = Path("/mnt/d/_outbox/reports/closed_loop")
SCHEMA = "openclaw.closed_loop_status.v1"

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|secret)\s*[:=]\s*[^,\s]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: f"{m.group(1)}=<redacted>" if m.lastindex else "<redacted>", redacted)
    return redacted


def run(command: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return {"ok": False, "exit": 127, "output": f"missing command: {exc.filename}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "exit": 124, "output": "timeout"}
    output = redact("\n".join(part for part in (result.stdout, result.stderr) if part).strip())
    return {"ok": result.returncode == 0, "exit": result.returncode, "output": output[:4000]}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def count_done_tasks() -> dict[str, Any]:
    tasks = ROOT / "TASKS.md"
    text = tasks.read_text(encoding="utf-8") if tasks.exists() else ""
    done_lines = re.findall(r"\[2026-06-\d{2} \d{2}:\d{2} \+08\].*Done:", text)
    recent_done = re.findall(r"\[2026-06-(?:08|09) \d{2}:\d{2} \+08\].*Done:", text)
    return {"total_june_done_events": len(done_lines), "recent_48h_done_events": len(recent_done)}


def github_publish_closure() -> dict[str, Any]:
    pr = run(["gh", "pr", "view", "16", "--json", "number,title,state,isDraft,url,headRefName,baseRefName,statusCheckRollup"], timeout=25)
    payload = None
    if pr["ok"]:
        try:
            payload = json.loads(pr["output"])
        except json.JSONDecodeError:
            payload = None
    return {
        "status": "active" if payload else "review",
        "draft_pr": payload,
        "scope_rule": "publish only exact staged files; never include runtime config or unrelated dirty worktree",
    }


def memory_closure() -> dict[str, Any]:
    memory_dir = ROOT / "memory"
    daily = memory_dir / "2026-06-09.md"
    protected = ["MEMORY.md", "DREAMS.md", "SOUL.md", "TOOLS.md", "AGENTS.md"]
    return {
        "status": "watch" if daily.exists() else "review",
        "canonical_daily_memory_exists": daily.exists(),
        "canonical_daily_memory": str(daily),
        "protected_bootstrap_files": [name for name in protected if (ROOT / name).exists()],
        "rule": "append durable facts to memory/YYYY-MM-DD.md; do not overwrite bootstrap/reference files",
    }


def validation_closure() -> dict[str, Any]:
    checks = [
        ["python3", "tools/observability.py", "--self-test"],
        ["python3", "tools/bot_error_doctor.py", "--self-test"],
        ["python3", "tools/system_status_overview.py", "--json"],
        ["python3", "tools/openclaw_primary_model.py", "--self-test"],
    ]
    results = [{"command": " ".join(command), **run(command, timeout=40)} for command in checks]
    return {
        "status": "pass" if all(item["ok"] for item in results) else "review",
        "checks": results,
    }


def evaluation_closure() -> dict[str, Any]:
    benchmark_tools = [
        "tools/real_task_golden_benchmark.py",
        "tools/photo_pipeline_benchmark.py",
        "tools/photo_real_sample_benchmark.py",
        "tools/openclaw_reflection_check.py",
    ]
    history = ROOT / "shared/artifacts/photo-benchmarks/history.jsonl"
    history_count = 0
    if history.exists():
        history_count = len([line for line in history.read_text(encoding="utf-8").splitlines() if line.strip()])
    return {
        "status": "watch",
        "benchmark_tools_present": [path for path in benchmark_tools if (ROOT / path).exists()],
        "photo_benchmark_history_entries": history_count,
        "missing_longitudinal_window": "7d/30d trend report not yet automated",
    }


def subagent_closure() -> dict[str, Any]:
    registry = load_json(ROOT / "agent_registry.json")
    expected = {"intel", "ops", "comms", "sentinel"}
    agents = set()
    if isinstance(registry, dict):
        raw = registry.get("agents", registry)
        if isinstance(raw, dict):
            agents = set(raw)
        elif isinstance(raw, list):
            agents = {str(item.get("id") or item.get("label")) for item in raw if isinstance(item, dict)}
    return {
        "status": "pass" if expected.issubset(agents) else "review",
        "expected_agents": sorted(expected),
        "registered_agents": sorted(agent for agent in agents if agent),
        "rotation_rule": "@ops executes; @sentinel reviews builds; @comms packages; @intel reviews factual accuracy",
    }


def browser_automation_closure() -> dict[str, Any]:
    candidates = [
        ROOT / "tools/browser_state_machine.py",
        ROOT / "tools/canva_web.mjs",
        ROOT / "tools/gemini_playwright_adapter.py",
        ROOT / "tools/google_poster.py",
    ]
    present = [str(path.relative_to(ROOT)) for path in candidates if path.exists()]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore")[:8000] for path in candidates if path.exists())
    resilience_hits = {
        "screenshot": "screenshot" in text.lower(),
        "fallback": "fallback" in text.lower(),
        "timeout": "timeout" in text.lower(),
        "selector": "selector" in text.lower(),
    }
    return {
        "status": "watch" if all(resilience_hits.values()) else "review",
        "tools_present": present,
        "resilience_signals": resilience_hits,
        "next_gap": "add per-site selector fallback matrices and screenshot-based failure classification",
    }


def collect() -> dict[str, Any]:
    sections = {
        "github_publish": github_publish_closure(),
        "memory": memory_closure(),
        "validation": validation_closure(),
        "evaluation": evaluation_closure(),
        "subagents": subagent_closure(),
        "browser_automation": browser_automation_closure(),
    }
    return {
        "schema": SCHEMA,
        "generated_at": now_iso(),
        "task_counts": count_done_tasks(),
        "overall": "review" if any(section.get("status") == "review" for section in sections.values()) else "watch",
        "sections": sections,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenClaw Closed-Loop Status",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- overall: `{report['overall']}`",
        f"- total_june_done_events: `{report['task_counts']['total_june_done_events']}`",
        f"- recent_48h_done_events: `{report['task_counts']['recent_48h_done_events']}`",
        "",
    ]
    titles = {
        "github_publish": "GitHub Publish Closure",
        "memory": "Memory Closure",
        "validation": "Validation Closure",
        "evaluation": "Evaluation Closure",
        "subagents": "Subagent Collaboration Closure",
        "browser_automation": "Browser Automation Closure",
    }
    for key, section in report["sections"].items():
        lines.extend([f"## {titles[key]}", "", f"- status: `{section.get('status')}`"])
        for item_key, value in section.items():
            if item_key == "status":
                continue
            if isinstance(value, (str, int, bool)) or value is None:
                lines.append(f"- {item_key}: `{value}`")
            else:
                lines.append(f"- {item_key}:")
                lines.append("```json")
                lines.append(json.dumps(value, indent=2, ensure_ascii=False)[:3000])
                lines.append("```")
        lines.append("")
    return "\n".join(lines)


def self_test() -> int:
    assert "abc" not in redact("secret=abc")
    sample = {
        "schema": SCHEMA,
        "generated_at": "2026-06-09T00:00:00+08:00",
        "overall": "watch",
        "task_counts": {"total_june_done_events": 1, "recent_48h_done_events": 1},
        "sections": {
            "github_publish": {"status": "active"},
            "memory": {"status": "watch"},
            "validation": {"status": "pass"},
            "evaluation": {"status": "watch"},
            "subagents": {"status": "pass"},
            "browser_automation": {"status": "watch"},
        },
    }
    rendered = render_markdown(sample)
    assert "GitHub Publish Closure" in rendered
    print("self_test=pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenClaw closed-loop status report")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown")
    parser.add_argument("--write", action="store_true", help="Write JSON and Markdown to D:\\_outbox\\reports\\closed_loop")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    report = collect()
    if args.write:
        OUTBOX.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        json_path = OUTBOX / f"closed_loop_status_{stamp}.json"
        md_path = OUTBOX / f"closed_loop_status_{stamp}.md"
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(f"json={json_path}")
        print(f"markdown={md_path}")
        return 0 if report["overall"] != "fail" else 1

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
