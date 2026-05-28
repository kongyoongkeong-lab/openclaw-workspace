#!/usr/bin/env python3
"""Read-only OpenClaw system health report.

This script probes local services without restarting, mutating, or writing state.
It intentionally redacts token-like material from command output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
N8N_DIR = ROOT / "n8n"
LANGFUSE_DIR = ROOT / "docker" / "langfuse"
MODEL_STATUS = ROOT / "tools" / "model_runtime_status.py"
GPU_CHECK = ROOT / "tools" / "check_gpu.sh"
HF_PREFLIGHT = ROOT / "tools" / "huggingface_preflight.py"

SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(r"(?i)((?:access|refresh|api|hf|openai|tavily|gateway)[_-]?token\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|password|secret|cookie)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
]


@dataclass
class CheckResult:
    name: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        def replace(match: re.Match[str]) -> str:
            if match.lastindex:
                return f"{match.group(1)}[REDACTED]"
            return "[REDACTED]"

        redacted = pattern.sub(replace, redacted)
    return redacted


def truncate(text: str, limit: int = 1400) -> str:
    text = redact(text.strip())
    if len(text) <= limit:
        return text
    return text[: limit - 24].rstrip() + "\n... [truncated]"


def run(command: list[str], timeout: int = 8, cwd: Path | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except FileNotFoundError:
        return 127, "command missing"
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except OSError as exc:
        return 1, str(exc)
    return completed.returncode, truncate(completed.stdout)


def http_get(url: str, timeout: float = 3.0) -> tuple[str, str, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": "openclaw-healthcheck/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(8192).decode("utf-8", errors="replace")
            return "ok", f"HTTP {response.status}", {"url": url, "body": truncate(body, 700)}
    except urllib.error.HTTPError as exc:
        body = exc.read(2048).decode("utf-8", errors="replace")
        return "warn" if exc.code < 500 else "fail", f"HTTP {exc.code}", {"url": url, "body": truncate(body, 500)}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return "fail", type(exc).__name__, {"url": url, "error": truncate(str(exc), 500)}


def tcp_probe(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def load_gateway_config() -> dict[str, Any]:
    if not OPENCLAW_CONFIG.exists():
        return {}
    try:
        config = json.loads(OPENCLAW_CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    gateway = config.get("gateway", {})
    return {
        "mode": gateway.get("mode", "unknown"),
        "bind": gateway.get("bind", "unknown"),
        "port": int(gateway.get("port", 18789)),
        "auth_mode": gateway.get("auth", {}).get("mode", "unknown"),
        "tailscale_mode": gateway.get("tailscale", {}).get("mode", "unknown"),
        "control_ui_allow_insecure_auth": gateway.get("controlUi", {}).get("allowInsecureAuth"),
    }


def check_gateway() -> CheckResult:
    info = load_gateway_config()
    port = int(info.get("port", 18789))
    port_open = tcp_probe("127.0.0.1", port)
    status = "ok" if port_open else "fail"
    details: dict[str, Any] = {"config": info, "tcp_127_0_0_1": port_open}
    if shutil.which("openclaw"):
        code, output = run(["openclaw", "gateway", "status"], timeout=8)
        details["openclaw_gateway_status_exit"] = code
        details["openclaw_gateway_status"] = output
        if code != 0 and status == "ok":
            status = "warn"
    return CheckResult("gateway", status, f"port {port} {'open' if port_open else 'closed'}", details)


def check_docker() -> CheckResult:
    if not shutil.which("docker"):
        return CheckResult("docker", "fail", "docker CLI missing")
    code, output = run(["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"], timeout=10)
    if code != 0:
        return CheckResult("docker", "fail", f"docker ps exit {code}", {"output": output})
    containers = [line for line in output.splitlines() if line.strip()]
    details: dict[str, Any] = {"containers": containers}
    for label, directory in (("n8n_compose", N8N_DIR), ("langfuse_compose", LANGFUSE_DIR)):
        compose_file = directory / "docker-compose.yml"
        if compose_file.exists():
            compose_code, compose_output = run(["docker", "compose", "ps"], timeout=10, cwd=directory)
            details[label] = {"exit": compose_code, "output": compose_output}
    summary = f"{len(containers)} running container(s)"
    return CheckResult("docker", "ok" if containers else "warn", summary, details)


def check_redis() -> CheckResult:
    if shutil.which("redis-cli"):
        code, output = run(["redis-cli", "-h", "127.0.0.1", "-p", "6379", "ping"], timeout=3)
        return CheckResult("redis", "ok" if code == 0 and "PONG" in output else "fail", output or f"exit {code}")
    port_open = tcp_probe("127.0.0.1", 6379)
    return CheckResult("redis", "ok" if port_open else "fail", "tcp 6379 open" if port_open else "tcp 6379 closed")


def check_http_service(name: str, url: str) -> CheckResult:
    status, summary, details = http_get(url)
    return CheckResult(name, status, summary, details)


def check_model_runtime() -> CheckResult:
    details: dict[str, Any] = {}
    status = "warn"
    if MODEL_STATUS.exists():
        code, output = run(["python3", str(MODEL_STATUS)], timeout=15)
        details["model_runtime_status"] = {"exit": code, "output": output}
        status = "ok" if code == 0 else "fail"
    if HF_PREFLIGHT.exists():
        code, output = run(["python3", str(HF_PREFLIGHT), "--list-only", "--no-write"], timeout=10)
        details["huggingface_preflight"] = {"exit": code, "output": output}
        if code not in (0, 2) and status == "ok":
            status = "warn"
    return CheckResult("model_runtime", status, "runtime snapshot collected", details)


def check_gpu() -> CheckResult:
    if GPU_CHECK.exists():
        code, output = run([str(GPU_CHECK)], timeout=8)
        status = "ok" if code == 0 else ("warn" if code == 2 else "fail")
        return CheckResult("gpu", status, "gpu preflight completed", {"exit": code, "output": output})
    if not shutil.which("nvidia-smi"):
        return CheckResult("gpu", "warn", "nvidia-smi missing")
    code, output = run(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        timeout=8,
    )
    return CheckResult("gpu", "ok" if code == 0 else "fail", "nvidia-smi snapshot", {"exit": code, "output": output})


def check_disk() -> CheckResult:
    paths = [ROOT, Path("/mnt/d")]
    rows: list[dict[str, Any]] = []
    status = "ok"
    for path in paths:
        if not path.exists():
            rows.append({"path": str(path), "status": "missing"})
            continue
        usage = shutil.disk_usage(path)
        used_pct = round((usage.used / usage.total) * 100, 1) if usage.total else 0
        rows.append(
            {
                "path": str(path),
                "total_gib": round(usage.total / (1024**3), 1),
                "free_gib": round(usage.free / (1024**3), 1),
                "used_pct": used_pct,
            }
        )
        if used_pct >= 90:
            status = "fail"
        elif used_pct >= 80 and status == "ok":
            status = "warn"
    return CheckResult("disk", status, "disk usage checked", {"paths": rows})


def collect_checks() -> list[CheckResult]:
    return [
        check_gateway(),
        check_docker(),
        check_http_service("n8n", "http://localhost:5678/healthz"),
        check_redis(),
        check_http_service("qdrant", "http://localhost:6333/collections"),
        check_http_service("comfyui", "http://127.0.0.1:8188/system_stats"),
        check_http_service("langfuse", "http://localhost:3000"),
        check_model_runtime(),
        check_gpu(),
        check_disk(),
    ]


def overall_status(checks: list[CheckResult]) -> str:
    statuses = {check.status for check in checks}
    if "fail" in statuses:
        return "fail"
    if "warn" in statuses:
        return "warn"
    return "ok"


def print_markdown(checks: list[CheckResult], show_details: bool) -> None:
    print("# OpenClaw System Health")
    print()
    print(f"- generated_at: `{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}`")
    print(f"- workspace: `{ROOT}`")
    print(f"- overall: `{overall_status(checks)}`")
    print("- mode: `read-only`")
    print()
    print("| Check | Status | Summary |")
    print("|---|---|---|")
    for check in checks:
        print(f"| `{check.name}` | `{check.status}` | {check.summary} |")
    if not show_details:
        return
    print()
    print("## Details")
    for check in checks:
        print()
        print(f"### {check.name}")
        print("```json")
        print(json.dumps(check.details, ensure_ascii=False, indent=2))
        print("```")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--details", action="store_true", help="Include redacted detailed output.")
    parser.add_argument("--fail-on-warn", action="store_true", help="Return non-zero for warn status.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checks = collect_checks()
    status = overall_status(checks)
    payload = {
        "schema": "openclaw.system_health.v1",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "workspace": str(ROOT),
        "mode": "read-only",
        "overall": status,
        "checks": [asdict(check) for check in checks],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_markdown(checks, args.details)
    if status == "fail":
        return 2
    if status == "warn" and args.fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
