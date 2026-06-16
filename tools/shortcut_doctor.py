#!/usr/bin/env python3
"""Read-only shortcut registry audit for local paths and safety metadata."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "shortcuts.md"
DEFAULT_OUT = Path("/mnt/d/_outbox/reports/shortcut_doctor")
DEFAULT_MANIFEST = ROOT / "config" / "shortcut_manifest.json"
DEFAULT_USAGE_LOG = ROOT / "data" / "shortcut_usage" / "shortcut_usage.jsonl"
PATH_RE = re.compile(r"`([^`]+)`")
COMMAND_PATH_RE = re.compile(
    r"(?<![\w./-])(?P<path>(?:python3\s+|node\s+|bash\s+|sh\s+)?(?:/home/jason2ykk/\.openclaw/workspace/)?(?:tools|scripts|skills|docs|config|protocols|memory)/[^\s`;|]+|(?:daily_news|daily_ai|SELF_UPGRADE_PROTOCOL|AGENTS|TASKS|shortcuts)\.md)"
)
STATUS_OK = {"已接入", "待接入", "待确认"}


@dataclass
class ShortcutRow:
    command: str
    aliases: str
    feature: str
    target: str
    status: str
    safety: str
    referenced_paths: list[str]
    missing_paths: list[str]
    warnings: list[str]
    capabilities: dict | None = None
    governance: dict | None = None


def split_md_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def strip_ticks(value: str) -> str:
    return value.replace("`", "").strip()


def normalize_reference(raw: str) -> str | None:
    value = raw.strip().strip(".,;:，。；：")
    if any(token in value for token in ("YYYY", "MM-DD", "<", ">")):
        return None
    try:
        tokens = shlex.split(value)
    except ValueError:
        tokens = value.split()
    if tokens and tokens[0] in {"python3", "python", "node", "bash", "sh"}:
        value = tokens[1] if len(tokens) > 1 else ""
    elif tokens:
        value = tokens[0]
    value = value.strip()
    if not value or value.startswith("--") or "<" in value or ">" in value:
        return None
    if value.startswith("C:\\") or value.startswith("D:\\"):
        return None
    if value.startswith("/home/jason2ykk/.openclaw/"):
        return value
    if value.startswith(("/mnt/", "/tmp/")):
        return value
    if value.startswith(("tools/", "scripts/", "skills/", "docs/", "config/", "protocols/", "memory/", "news/", "shared/", "data/")):
        return str(ROOT / value)
    if value in {"daily_news.md", "daily_ai.md", "SELF_UPGRADE_PROTOCOL.md", "AGENTS.md", "TASKS.md", "shortcuts.md"}:
        return str(ROOT / value)
    return None


def extract_references(text: str) -> list[str]:
    refs: list[str] = []
    candidates = PATH_RE.findall(text)
    candidates.extend(match.group("path") for match in COMMAND_PATH_RE.finditer(text))
    for candidate in candidates:
        ref = normalize_reference(candidate)
        if ref and ref not in refs:
            refs.append(ref)
    valid_refs = [ref for ref in refs if Path(ref).exists()]
    filtered: list[str] = []
    for ref in refs:
        if (
            ref.startswith(str(ROOT / "skills"))
            and not Path(ref).exists()
            and any(valid.endswith(ref.removeprefix(str(ROOT) + "/")) for valid in valid_refs)
        ):
            continue
        filtered.append(ref)
    return filtered


def parse_shortcuts(path: Path) -> list[ShortcutRow]:
    rows: list[ShortcutRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = split_md_row(line)
        if len(cells) < 6 or cells[0] == "---":
            continue
        command, aliases, feature, target, status, safety = cells[:6]
        refs = extract_references(target)
        missing = [ref for ref in refs if not Path(ref).exists()]
        warnings: list[str] = []
        status_text = strip_ticks(status)
        if status_text not in STATUS_OK:
            warnings.append(f"unexpected status: {status_text}")
        if status_text == "已接入" and missing:
            warnings.append("connected shortcut references missing local paths")
        high_risk_words = ("token", "API key", "备份", "重启", "Qdrant", "push", "delete", "download", "upload")
        if any(word.lower() in (target + safety).lower() for word in high_risk_words):
            if not any(word in safety for word in ("确认", "只读", "严禁", "不输出", "不上传", "不改", "需确认", "明确要求", "直接执行", "短暂离线")):
                warnings.append("high-risk wording lacks explicit safety gate")
        rows.append(
            ShortcutRow(
                command=strip_ticks(command),
                aliases=aliases,
                feature=feature,
                target=target,
                status=status_text,
                safety=safety,
                referenced_paths=refs,
                missing_paths=missing,
                warnings=warnings,
            )
        )
    return rows


def read_small(path: Path, limit: int = 120_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def script_refs(row: ShortcutRow) -> list[str]:
    suffixes = (".py", ".mjs", ".js", ".sh", ".bat", ".ps1")
    return [ref for ref in row.referenced_paths if Path(ref).suffix.lower() in suffixes]


def alias_list(row: ShortcutRow) -> list[str]:
    values = [strip_ticks(part) for part in row.aliases.split(",")]
    return [value for value in values if value and value != "-"]


def display_path(raw: str | None) -> str | None:
    if not raw:
        return None
    path = Path(raw)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return raw


def output_paths(row: ShortcutRow) -> list[str]:
    text = f"{row.target}\n{row.safety}"
    paths: list[str] = []
    for match in re.finditer(r"(?:[A-Z]:\\|/mnt/[a-z]/)[^\s`；;，,。)）]+", text):
        value = match.group(0).rstrip("\\/")
        if value not in paths:
            paths.append(value)
    for candidate in PATH_RE.findall(text):
        ref = normalize_reference(candidate)
        if not ref:
            continue
        ref_path = Path(ref)
        try:
            include = any(ref_path.resolve().is_relative_to(root) for root in (ROOT / "config", ROOT / "data", ROOT / "news", ROOT / "shared"))
        except OSError:
            include = False
        if include:
            value = display_path(ref) or ref
            if value not in paths:
                paths.append(value)
    output_roots = (ROOT / "config", ROOT / "data", ROOT / "news", ROOT / "shared")
    for ref in row.referenced_paths:
        ref_path = Path(ref)
        include = any(part in ref for part in ("/reports/", "/shared/artifacts/", "/media/outbound"))
        try:
            include = include or any(ref_path.resolve().is_relative_to(root) for root in output_roots)
        except OSError:
            pass
        if include:
            value = display_path(ref) or ref
            if value not in paths:
                paths.append(value)
    return paths


def infer_group(row: ShortcutRow) -> str:
    text = f"{row.command} {row.aliases} {row.feature} {row.target}".lower()
    if any(term in text for term in ("照片", "图片", "海报", "comfy", "gemini海报", "电脑海报", "抠图")):
        return "photo"
    if any(term in text for term in ("豆包", "doubao")):
        return "automation"
    if any(term in text for term in ("模型", "codex", "deepseek", "额度", "context", "路由")):
        return "model"
    if any(term in text for term in ("备份", "归档")):
        return "backup"
    if any(term in text for term in ("新闻", "ai日报", "tavily", "塔维")):
        return "news"
    if any(term in text for term in ("github", "仓库", "git")):
        return "github"
    if any(term in text for term in ("浏览器", "chrome", "pdf", "ahk", "automation", "gateway", "网关", "服务", "日志")):
        return "system"
    return "system"


def high_risk_pending_reason(row: ShortcutRow) -> str | None:
    text = f"{row.command}\n{row.aliases}\n{row.feature}\n{row.target}\n{row.safety}".lower()
    read_only_context = "只读" in row.safety or "不执行" in row.safety
    checks = (
        ("gateway_restart", ("重启网关", "gateway restart")),
        ("profile_switch", ("额度切换", "账号切换", "profile switch", "codex切换")),
        ("model_default_change", ("codex主用", "deepseek主用", "api模型", "本地模型", "混合模型", "主模型", "model default")),
        ("backup_restore", ("备份", "restore", "恢复")),
        ("n8n_activation", ("n8n activation", "workflow activation", "激活")),
        ("browser_live_generation", ("live", "confirm-live", "submit", "提交", "上传", "出图", "下载收割")),
        ("credential_change", ("credential change", "token change", "oauth change", "api key change", "密钥变更", "凭证变更")),
        ("delete_move_files", ("delete", "remove", "move", "删除", "移动")),
    )
    for reason, terms in checks:
        if any(term in text for term in terms):
            if read_only_context and reason not in {"credential_change", "delete_move_files"}:
                continue
            return reason
    return None


def infer_risk(row: ShortcutRow) -> str:
    text = f"{row.target}\n{row.safety}".lower()
    local_only = any(term in text for term in ("纯本地", "默认全本地", "不调用 cdp", "不调用cdp", "不调用 api", "不调用api", "不调用 cdp/gemini"))
    pending_reason = high_risk_pending_reason(row)
    if pending_reason in {"credential_change", "delete_move_files"}:
        return "dangerous"
    if row.status == "待确认" or "待确认" in row.safety or "必须 jason 明确确认" in text or "执行前必须" in row.safety:
        return "confirmation_required"
    if pending_reason:
        return "confirmation_required"
    if "只读" in row.safety or "不执行" in row.safety:
        return "read_only"
    if not local_only and any(term in text for term in ("live", "cdp", "browser", "gemini", "豆包", "canva", "suno", "上传", "提交")):
        return "live_external"
    if any(term in text for term in ("set ", "下载", "生成", "切换", "写入", "输出", "归档")):
        return "side_effecting"
    return "low_write"


def approval_class_for(row: ShortcutRow) -> str:
    reason = high_risk_pending_reason(row)
    if reason in {"credential_change", "delete_move_files"}:
        return "operator_only"
    if reason in {"gateway_restart", "profile_switch", "model_default_change", "backup_restore", "n8n_activation", "browser_live_generation"}:
        return "confirm_each_run"
    if row.status == "待确认":
        return "confirm_each_run"
    return "none"


def classify_safety(row: ShortcutRow) -> str:
    text = f"{row.target}\n{row.safety}"
    if row.status != "已接入":
        return "not_connected"
    if infer_risk(row) == "confirmation_required":
        return "confirmation_required"
    if "只读" in row.safety or "不执行" in row.safety:
        return "read_only"
    if any(word in text for word in ("重启", "set ", "下载", "上传", "生成", "切换")):
        return "side_effecting"
    return "callable"


def detect_script_support(paths: list[str], row: ShortcutRow | None = None) -> dict:
    has_help = False
    has_self_test = False
    has_dry_run = False
    inspected: list[str] = []
    support_text = ""
    if row is not None:
        support_text = f"{row.command}\n{row.feature}\n{row.target}\n{row.safety}".lower()
    for raw in paths:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            continue
        inspected.append(raw)
        text = read_small(path).lower()
        if any(term in text for term in ("argparse", "--help", "commander", "usage:", "help=")):
            has_help = True
        if any(term in text for term in ("self-test", "self_test", "selftest")):
            has_self_test = True
        if any(term in text for term in ("dry-run", "dry_run", "--list-only", "--no-write", "read-only", "只读")):
            has_dry_run = True
    if any(term in support_text for term in ("self-test", "self_test", "selftest")):
        has_self_test = True
    if any(term in support_text for term in ("--dry-run", "dry-run", "--list-only", "--no-write", "--profiles-only", "plan only", "确认前")):
        has_dry_run = True
    return {
        "inspected_scripts": inspected,
        "has_help_hint": has_help,
        "has_self_test_hint": has_self_test,
        "has_dry_run_hint": has_dry_run,
    }


def add_deep_capabilities(rows: list[ShortcutRow]) -> None:
    for row in rows:
        scripts = script_refs(row)
        row.capabilities = {
            "safety_class": classify_safety(row),
            "referenced_script_count": len(scripts),
            "referenced_scripts": scripts,
            **detect_script_support(scripts, row),
        }
        row.governance = build_governance(row)


def build_governance(row: ShortcutRow) -> dict:
    risk = infer_risk(row)
    needs_confirm = risk in {"confirmation_required", "dangerous"} or approval_class_for(row) != "none"
    return {
        "group": infer_group(row),
        "risk": risk,
        "needs_confirm": needs_confirm,
        "approval_class": approval_class_for(row),
        "pending_action_reason": high_risk_pending_reason(row),
        "output_paths": output_paths(row),
    }


def recent_fail_counts(log_path: Path = DEFAULT_USAGE_LOG, limit: int = 100) -> dict[str, int]:
    if not log_path.exists():
        return {}
    counts: dict[str, int] = {}
    try:
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    except OSError:
        return {}
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("status") == "fail":
            shortcut = str(item.get("shortcut") or "").strip()
            if shortcut:
                counts[shortcut] = counts.get(shortcut, 0) + 1
    return counts


def apply_quarantine(rows: list[ShortcutRow], log_path: Path = DEFAULT_USAGE_LOG) -> None:
    counts = recent_fail_counts(log_path)
    for row in rows:
        aliases = [row.command, *alias_list(row)]
        failures = max([counts.get(alias, 0) for alias in aliases] or [0])
        if failures >= 3:
            if row.governance is None:
                row.governance = build_governance(row)
            row.governance["quarantined"] = True
            row.governance["recent_failures"] = failures
        elif row.governance is not None:
            row.governance["quarantined"] = False
            row.governance["recent_failures"] = failures


def alias_collisions(rows: list[ShortcutRow]) -> list[dict]:
    seen: dict[str, list[str]] = {}
    for row in rows:
        for value in [row.command, *alias_list(row)]:
            key = value.casefold()
            seen.setdefault(key, []).append(row.command)
    collisions = []
    for alias, commands in seen.items():
        unique = sorted(set(commands))
        if len(unique) > 1:
            collisions.append({"alias": alias, "commands": unique})
    return collisions


def fix_suggestions(rows: list[ShortcutRow]) -> list[dict]:
    suggestions: list[dict] = []
    for row in rows:
        caps = row.capabilities or {}
        gov = row.governance or build_governance(row)
        issues: list[str] = []
        scripts = caps.get("referenced_script_count", 0)
        if scripts and not caps.get("has_help_hint"):
            issues.append("missing help")
        if scripts and gov["risk"] in {"side_effecting", "live_external", "confirmation_required", "dangerous"} and not caps.get("has_dry_run_hint"):
            issues.append("missing dry-run")
        if scripts and not caps.get("has_self_test_hint"):
            issues.append("missing self-test")
        if gov["risk"] not in {"read_only", "low_write", "side_effecting", "confirmation_required", "live_external", "dangerous"}:
            issues.append("missing risk class")
        if gov["risk"] in {"confirmation_required", "dangerous"} and not gov.get("needs_confirm"):
            issues.append("missing confirmation gate")
        if gov["risk"] in {"side_effecting", "live_external", "confirmation_required"} and not gov.get("output_paths"):
            issues.append("missing output evidence")
        if issues:
            suggestions.append(
                {
                    "shortcut": row.command,
                    "group": gov["group"],
                    "risk": gov["risk"],
                    "issues": issues,
                    "recommendation": "Add explicit metadata or script support; do not auto-fix.",
                }
            )
    return suggestions


def summarize(rows: Iterable[ShortcutRow]) -> dict:
    data = list(rows)
    missing_rows = [row for row in data if row.missing_paths]
    warning_rows = [row for row in data if row.warnings]
    by_status: dict[str, int] = {}
    for row in data:
        by_status[row.status] = by_status.get(row.status, 0) + 1
    safety_classes: dict[str, int] = {}
    script_rows = 0
    help_rows = 0
    self_test_rows = 0
    dry_run_rows = 0
    for row in data:
        caps = row.capabilities or {}
        safety_class = caps.get("safety_class")
        if safety_class:
            safety_classes[safety_class] = safety_classes.get(safety_class, 0) + 1
        if caps.get("referenced_script_count", 0):
            script_rows += 1
        if caps.get("has_help_hint"):
            help_rows += 1
        if caps.get("has_self_test_hint"):
            self_test_rows += 1
        if caps.get("has_dry_run_hint"):
            dry_run_rows += 1
    governance_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    confirm_count = 0
    quarantined = 0
    for row in data:
        gov = row.governance or build_governance(row)
        governance_counts[gov["risk"]] = governance_counts.get(gov["risk"], 0) + 1
        group_counts[gov["group"]] = group_counts.get(gov["group"], 0) + 1
        if gov.get("needs_confirm"):
            confirm_count += 1
        if gov.get("quarantined"):
            quarantined += 1
    collisions = alias_collisions(data)
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "total": len(data),
        "by_status": by_status,
        "missing_path_count": sum(len(row.missing_paths) for row in data),
        "rows_with_missing_paths": len(missing_rows),
        "rows_with_warnings": len(warning_rows),
        "deep": {
            "enabled": any(row.capabilities for row in data),
            "safety_classes": safety_classes,
            "rows_with_scripts": script_rows,
            "rows_with_help_hint": help_rows,
            "rows_with_self_test_hint": self_test_rows,
            "rows_with_dry_run_hint": dry_run_rows,
        },
        "governance": {
            "risk_classes": governance_counts,
            "groups": group_counts,
            "needs_confirm": confirm_count,
            "alias_collision_count": len(collisions),
            "alias_collisions": collisions,
            "quarantined": quarantined,
        },
    }


def write_reports(out_dir: Path, rows: list[ShortcutRow], summary: dict) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "shortcut_doctor.json"
    md_path = out_dir / "shortcut_doctor.md"
    payload = {"summary": summary, "rows": [asdict(row) for row in rows]}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Shortcut Doctor",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- total: `{summary['total']}`",
        f"- by_status: `{summary['by_status']}`",
        f"- missing_path_count: `{summary['missing_path_count']}`",
        f"- rows_with_warnings: `{summary['rows_with_warnings']}`",
    ]
    if summary.get("deep", {}).get("enabled"):
        deep = summary["deep"]
        lines.extend(
            [
                f"- safety_classes: `{deep['safety_classes']}`",
                f"- rows_with_scripts: `{deep['rows_with_scripts']}`",
                f"- rows_with_help_hint: `{deep['rows_with_help_hint']}`",
                f"- rows_with_self_test_hint: `{deep['rows_with_self_test_hint']}`",
                f"- rows_with_dry_run_hint: `{deep['rows_with_dry_run_hint']}`",
            ]
        )
    governance = summary.get("governance", {})
    if governance:
        lines.extend(
            [
                f"- governance_risk_classes: `{governance.get('risk_classes', {})}`",
                f"- governance_groups: `{governance.get('groups', {})}`",
                f"- needs_confirm: `{governance.get('needs_confirm', 0)}`",
                f"- alias_collision_count: `{governance.get('alias_collision_count', 0)}`",
                f"- quarantined: `{governance.get('quarantined', 0)}`",
            ]
        )
    lines.extend(["", "## Findings"])
    findings = [row for row in rows if row.missing_paths or row.warnings]
    if not findings:
        lines.append("- PASS: no missing local paths or shortcut metadata warnings.")
    for row in findings:
        lines.append(f"- `{row.command}`: status={row.status}")
        for missing in row.missing_paths:
            lines.append(f"  - missing: `{missing}`")
        for warning in row.warnings:
            lines.append(f"  - warning: {warning}")
    if summary.get("deep", {}).get("enabled"):
        lines.extend(["", "## Capability Matrix"])
        for row in rows:
            caps = row.capabilities or {}
            lines.append(
                "- `{}`: class={}, scripts={}, help={}, self_test={}, dry_run={}".format(
                    row.command,
                    caps.get("safety_class", "unknown"),
                    caps.get("referenced_script_count", 0),
                    caps.get("has_help_hint", False),
                    caps.get("has_self_test_hint", False),
                    caps.get("has_dry_run_hint", False),
                )
            )
    suggestions = fix_suggestions(rows)
    lines.extend(["", "## Fix Suggestions"])
    if not suggestions:
        lines.append("- PASS: no safe fix suggestions.")
    for item in suggestions:
        lines.append(
            f"- `{item['shortcut']}`: group={item['group']}, risk={item['risk']}, issues={', '.join(item['issues'])}"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def build_manifest(rows: list[ShortcutRow]) -> dict:
    if not any(row.capabilities for row in rows):
        add_deep_capabilities(rows)
    apply_quarantine(rows)
    shortcuts = []
    for index, row in enumerate(rows, start=1):
        gov = row.governance or build_governance(row)
        caps = dict(row.capabilities or {})
        for key in ("referenced_scripts", "inspected_scripts"):
            if key in caps:
                caps[key] = [display_path(item) or item for item in caps[key]]
        scripts = script_refs(row)
        first_script = scripts[0] if scripts else None
        display_script = display_path(first_script)
        shortcuts.append(
            {
                "id": f"shortcut_{index:03d}",
                "name": row.command,
                "aliases": alias_list(row),
                "group": gov["group"],
                "script": display_script,
                "args_template": row.target,
                "risk": gov["risk"],
                "needs_confirm": gov["needs_confirm"],
                "approval_class": gov["approval_class"],
                "pending_action_reason": gov["pending_action_reason"],
                "dry_run_command": None,
                "self_test_command": None,
                "help_command": f"python3 {display_script} --help" if display_script and display_script.endswith(".py") else None,
                "output_paths": gov["output_paths"],
                "owner": "@main",
                "status": row.status,
                "last_checked": datetime.now().astimezone().isoformat(timespec="seconds"),
                "quarantined": gov.get("quarantined", False),
                "recent_failures": gov.get("recent_failures", 0),
                "capabilities": caps,
            }
        )
    return {
        "schema": "openclaw.shortcut_manifest.v1",
        "source": display_path(str(DEFAULT_REGISTRY)) or str(DEFAULT_REGISTRY),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "risk_policy": ["read_only", "low_write", "side_effecting", "confirmation_required", "live_external", "dangerous"],
        "approval_classes": ["none", "confirm_once", "confirm_each_run", "confirm_with_expiry", "operator_only"],
        "summary": summarize(rows),
        "shortcuts": shortcuts,
    }


def cmd_audit(args: argparse.Namespace) -> int:
    rows = parse_shortcuts(args.registry)
    if args.deep:
        add_deep_capabilities(rows)
    else:
        for row in rows:
            row.governance = build_governance(row)
    apply_quarantine(rows)
    summary = summarize(rows)
    if args.json:
        print(json.dumps({"summary": summary, "rows": [asdict(row) for row in rows]}, indent=2, ensure_ascii=False))
    else:
        print(f"total={summary['total']}")
        print(f"by_status={summary['by_status']}")
        print(f"missing_path_count={summary['missing_path_count']}")
        print(f"rows_with_warnings={summary['rows_with_warnings']}")
        if args.deep:
            deep = summary["deep"]
            print(f"safety_classes={deep['safety_classes']}")
            print(f"rows_with_scripts={deep['rows_with_scripts']}")
            print(f"rows_with_help_hint={deep['rows_with_help_hint']}")
            print(f"rows_with_self_test_hint={deep['rows_with_self_test_hint']}")
            print(f"rows_with_dry_run_hint={deep['rows_with_dry_run_hint']}")
        governance = summary["governance"]
        print(f"governance_risk_classes={governance['risk_classes']}")
        print(f"governance_groups={governance['groups']}")
        print(f"needs_confirm={governance['needs_confirm']}")
        print(f"alias_collision_count={governance['alias_collision_count']}")
        print(f"quarantined={governance['quarantined']}")
        if args.fix_suggestions:
            suggestions = fix_suggestions(rows)
            print(f"fix_suggestion_count={len(suggestions)}")
            for item in suggestions:
                print(f"fix_suggestion={item['shortcut']}|{item['risk']}|{','.join(item['issues'])}")
    if not args.no_write:
        json_path, md_path = write_reports(args.out, rows, summary)
        print(f"json_report={json_path}")
        print(f"markdown_report={md_path}")
    connected_missing = any(row.status == "已接入" and row.missing_paths for row in rows)
    return 1 if connected_missing else 0


def cmd_manifest(args: argparse.Namespace) -> int:
    rows = parse_shortcuts(args.registry)
    add_deep_capabilities(rows)
    apply_quarantine(rows)
    payload = build_manifest(rows)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"manifest={args.write}")
    if args.json or not args.write:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_self_test(_: argparse.Namespace) -> int:
    sample = """# Registry

| 指令 | 别名 | 功能 | 执行路径 / 处理方式 | 状态 | 安全规则 |
|---|---|---|---|---|---|
| `测试` | - | ok | `tools/shortcut_doctor.py` | 已接入 | 只读 |
| `缺失` | - | bad | `tools/not_real.py` | 已接入 | 只读 |
"""
    with tempfile.TemporaryDirectory() as tmp:
        registry = Path(tmp) / "shortcuts.md"
        registry.write_text(sample, encoding="utf-8")
        rows = parse_shortcuts(registry)
        add_deep_capabilities(rows)
        assert len(rows) == 2
        assert rows[0].missing_paths == []
        assert rows[1].missing_paths
        assert rows[0].capabilities["referenced_script_count"] == 1
        assert rows[0].governance["risk"] == "read_only"
        summary = summarize(rows)
        assert summary["missing_path_count"] == 1
        assert summary["deep"]["enabled"] is True
        assert build_manifest(rows)["schema"] == "openclaw.shortcut_manifest.v1"
    print("PASS: shortcut doctor self-test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Audit shortcuts.md")
    audit_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    audit_parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    audit_parser.add_argument("--json", action="store_true")
    audit_parser.add_argument("--no-write", action="store_true")
    audit_parser.add_argument("--deep", action="store_true", help="Add static capability matrix without running target commands")
    audit_parser.add_argument("--fix-suggestions", action="store_true", help="Print safe recommendation-only governance suggestions")
    audit_parser.set_defaults(func=cmd_audit)

    manifest_parser = subparsers.add_parser("manifest", help="Generate structured shortcut manifest")
    manifest_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    manifest_parser.add_argument("--write", type=Path, default=DEFAULT_MANIFEST)
    manifest_parser.add_argument("--json", action="store_true")
    manifest_parser.set_defaults(func=cmd_manifest)

    self_test_parser = subparsers.add_parser("self-test", help="Run deterministic self-test")
    self_test_parser.set_defaults(func=cmd_self_test)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
