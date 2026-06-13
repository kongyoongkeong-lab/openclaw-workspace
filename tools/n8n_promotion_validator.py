#!/usr/bin/env python3
"""Read-only n8n workflow promotion validator.

Checks saved n8n workflow JSON before temporary activation or promotion. The
validator intentionally performs no workflow activation, mutation, restart, or
remote Git operation.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW_DIR = ROOT / "n8n" / "workflows"
WEBHOOK_NODE_TYPE = "n8n-nodes-base.webhook"
SAFE_WEBHOOK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{5,127}$")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str | None = None
    node: str | None = None


@dataclass
class ValidationResult:
    ok: bool
    checked_workflows: list[str]
    webhook_nodes: int
    findings: list[Finding]
    db_rows: list[dict[str, str | None]]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_workflow(path: Path) -> tuple[dict, list[Finding]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [Finding("fail", "json_invalid", f"invalid JSON: {exc}", rel(path))]
    if not isinstance(data, dict):
        return {}, [Finding("fail", "json_not_object", "workflow JSON root must be an object", rel(path))]
    return data, []


def validate_workflow(path: Path, require_inactive: bool) -> tuple[int, list[Finding]]:
    data, findings = load_workflow(path)
    if findings:
        return 0, findings

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        return 0, [Finding("fail", "nodes_missing", "workflow must contain a nodes array", rel(path))]

    if require_inactive and data.get("active") is not False:
        findings.append(Finding("fail", "workflow_active", "workflow JSON must have active=false before promotion validation", rel(path)))

    webhook_count = 0
    seen_ids: dict[str, str] = {}
    seen_routes: dict[tuple[str, str], str] = {}
    for node in nodes:
        if not isinstance(node, dict) or node.get("type") != WEBHOOK_NODE_TYPE:
            continue
        webhook_count += 1
        node_name = str(node.get("name") or node.get("id") or "<unnamed>")
        params = node.get("parameters") if isinstance(node.get("parameters"), dict) else {}
        webhook_id = node.get("webhookId")
        path_value = params.get("path")
        method = str(params.get("httpMethod") or "GET").upper()

        if not isinstance(webhook_id, str) or not webhook_id.strip():
            findings.append(Finding("fail", "webhook_id_missing", "Webhook node must include a stable top-level webhookId", rel(path), node_name))
        elif not SAFE_WEBHOOK_ID.fullmatch(webhook_id):
            findings.append(Finding("fail", "webhook_id_unsafe", "webhookId must be 6-128 URL-safe characters", rel(path), node_name))
        elif webhook_id in seen_ids:
            findings.append(Finding("fail", "webhook_id_duplicate", f"webhookId duplicates node {seen_ids[webhook_id]}", rel(path), node_name))
        else:
            seen_ids[webhook_id] = node_name

        if not isinstance(path_value, str) or not path_value.strip():
            findings.append(Finding("fail", "webhook_path_missing", "Webhook node must include a non-empty parameters.path", rel(path), node_name))
        else:
            normalized_path = path_value.strip().strip("/")
            if normalized_path.startswith("webhook/") or normalized_path.startswith("webhook-test/"):
                findings.append(Finding("fail", "webhook_path_prefixed", "parameters.path must omit webhook/webhook-test prefix", rel(path), node_name))
            route_key = (method, normalized_path)
            if route_key in seen_routes:
                findings.append(Finding("fail", "webhook_route_duplicate", f"route duplicates node {seen_routes[route_key]}", rel(path), node_name))
            else:
                seen_routes[route_key] = node_name

    if webhook_count == 0:
        findings.append(Finding("warn", "webhook_node_absent", "workflow contains no Webhook node", rel(path)))
    return webhook_count, findings


def query_db_webhooks(workflow_id: str | None) -> tuple[list[dict[str, str | None]], list[Finding]]:
    sql = 'select "workflowId","webhookPath",method,node,"webhookId" from webhook_entity'
    if workflow_id:
        escaped = workflow_id.replace("'", "''")
        sql += f" where \"workflowId\" = '{escaped}'"
    sql += ' order by "workflowId","webhookPath",method,node;'
    cmd = [
        "docker",
        "exec",
        "n8n-postgres-1",
        "psql",
        "-U",
        "n8n_user",
        "-d",
        "pentagon_n8n",
        "-t",
        "-A",
        "-F",
        "\t",
        "-c",
        sql,
    ]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=15, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return [], [Finding("fail", "db_query_failed", f"could not query n8n webhook_entity read-only: {exc}")]
    if proc.returncode != 0:
        stderr = proc.stderr.strip().splitlines()
        detail = stderr[-1] if stderr else "psql returned non-zero status"
        return [], [Finding("fail", "db_query_failed", detail)]

    rows: list[dict[str, str | None]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        while len(parts) < 5:
            parts.append("")
        rows.append(
            {
                "workflowId": parts[0] or None,
                "webhookPath": parts[1] or None,
                "method": parts[2] or None,
                "node": parts[3] or None,
                "webhookId": parts[4] or None,
            }
        )
    return rows, []


def validate(paths: list[Path], require_inactive: bool, check_db: bool, workflow_id: str | None) -> ValidationResult:
    findings: list[Finding] = []
    checked: list[str] = []
    webhook_nodes = 0
    for path in paths:
        checked.append(rel(path))
        count, path_findings = validate_workflow(path, require_inactive=require_inactive)
        webhook_nodes += count
        findings.extend(path_findings)

    db_rows: list[dict[str, str | None]] = []
    if check_db:
        db_rows, db_findings = query_db_webhooks(workflow_id)
        findings.extend(db_findings)
        if workflow_id and db_rows:
            findings.append(
                Finding(
                    "fail",
                    "db_stale_webhook_rows",
                    f"workflow {workflow_id} has {len(db_rows)} webhook_entity row(s); expected 0 before inactive draft promotion",
                )
            )

    ok = not any(item.level == "fail" for item in findings)
    return ValidationResult(ok=ok, checked_workflows=checked, webhook_nodes=webhook_nodes, findings=findings, db_rows=db_rows)


def workflow_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(item) for item in args.workflow]
    if args.all:
        paths.extend(sorted(DEFAULT_WORKFLOW_DIR.glob("*.json")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path if path.is_absolute() else ROOT / path
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    if not unique:
        raise SystemExit("Provide --workflow PATH or --all")
    missing = [rel(path) for path in unique if not path.exists()]
    if missing:
        raise SystemExit(f"Missing workflow file(s): {', '.join(missing)}")
    return unique


def print_human(result: ValidationResult) -> None:
    print("# n8n Promotion Validator")
    print(f"checked_workflows={len(result.checked_workflows)}")
    print(f"webhook_nodes={result.webhook_nodes}")
    print(f"db_rows={len(result.db_rows)}")
    if result.findings:
        print("\n## Findings")
        for item in result.findings:
            location = f" {item.path}" if item.path else ""
            node = f" [{item.node}]" if item.node else ""
            print(f"- {item.level.upper()}: {item.code}:{location}{node} {item.message}")
    print("\nPASS: n8n promotion gate passed." if result.ok else "\nFAIL: n8n promotion gate blocked promotion.")


def self_test() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        good = base / "good.json"
        bad = base / "bad.json"
        duplicate = base / "duplicate.json"
        good.write_text(
            json.dumps(
                {
                    "active": False,
                    "nodes": [
                        {
                            "name": "Webhook",
                            "type": WEBHOOK_NODE_TYPE,
                            "webhookId": "abc123-stable",
                            "parameters": {"path": "pentagon/test", "httpMethod": "POST"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        bad.write_text(
            json.dumps(
                {
                    "active": False,
                    "nodes": [
                        {
                            "name": "Webhook",
                            "type": WEBHOOK_NODE_TYPE,
                            "parameters": {"path": "webhook/pentagon/test", "httpMethod": "POST"},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        duplicate.write_text(
            json.dumps(
                {
                    "active": False,
                    "nodes": [
                        {
                            "name": "Webhook A",
                            "type": WEBHOOK_NODE_TYPE,
                            "webhookId": "abc123-stable",
                            "parameters": {"path": "pentagon/test", "httpMethod": "POST"},
                        },
                        {
                            "name": "Webhook B",
                            "type": WEBHOOK_NODE_TYPE,
                            "webhookId": "abc123-stable",
                            "parameters": {"path": "pentagon/test", "httpMethod": "POST"},
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        if not validate([good], require_inactive=True, check_db=False, workflow_id=None).ok:
            failures.append("valid workflow was rejected")
        bad_result = validate([bad], require_inactive=True, check_db=False, workflow_id=None)
        bad_codes = {item.code for item in bad_result.findings}
        if bad_result.ok or "webhook_id_missing" not in bad_codes or "webhook_path_prefixed" not in bad_codes:
            failures.append("missing webhookId or prefixed path was not rejected")
        duplicate_result = validate([duplicate], require_inactive=True, check_db=False, workflow_id=None)
        duplicate_codes = {item.code for item in duplicate_result.findings}
        if duplicate_result.ok or "webhook_id_duplicate" not in duplicate_codes or "webhook_route_duplicate" not in duplicate_codes:
            failures.append("duplicate webhook id/route was not rejected")

    print("# n8n Promotion Validator Self-Test")
    if failures:
        print("\n## Failures")
        for item in failures:
            print(f"- FAIL: {item}")
        return 1
    print("\nPASS: deterministic n8n promotion validator self-test passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", action="append", default=[], help="saved workflow JSON to validate")
    parser.add_argument("--all", action="store_true", help="validate all n8n/workflows/*.json files")
    parser.add_argument("--require-inactive", action="store_true", default=True, help="require workflow JSON active=false")
    parser.add_argument("--no-require-inactive", dest="require_inactive", action="store_false")
    parser.add_argument("--check-db", action="store_true", help="read n8n Postgres webhook_entity rows")
    parser.add_argument("--workflow-id", help="workflow id expected to have zero webhook_entity rows before promotion")
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    parser.add_argument("--self-test", action="store_true", help="run deterministic self-test")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    result = validate(workflow_paths(args), args.require_inactive, args.check_db, args.workflow_id)
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print_human(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
