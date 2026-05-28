#!/usr/bin/env python3
"""Read-only photo processing capability snapshot for OpenClaw.

The checker intentionally avoids installing packages, starting services, or
touching image files. It reports the current local toolchain so photo dialog
routes can make conservative decisions.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
COMFY_URL = "http://127.0.0.1:8188/system_stats"


@dataclass
class Check:
    name: str
    status: str
    detail: str


def run(command: list[str], timeout: int = 8) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return result.returncode, output


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def command_check(name: str, command: str, version_args: list[str] | None = None) -> Check:
    path = shutil.which(command)
    if not path:
        return Check(name, "missing", f"{command} not found")
    if not version_args:
        return Check(name, "ok", path)
    code, output = run([command, *version_args])
    detail = first_line(output) or path
    return Check(name, "ok" if code == 0 else "warn", detail)


def module_check(module: str, package: str | None = None) -> Check:
    dist_name = package or module
    try:
        version = importlib.metadata.version(dist_name)
    except importlib.metadata.PackageNotFoundError:
        return Check(module, "missing", f"{dist_name} not installed")
    return Check(module, "ok", version)


def file_check(name: str, path: Path) -> Check:
    if path.exists():
        return Check(name, "ok", str(path.relative_to(ROOT)))
    return Check(name, "missing", str(path.relative_to(ROOT)))


def gpu_check() -> Check:
    checker = ROOT / "tools" / "check_gpu.sh"
    if not checker.exists():
        return Check("gpu", "missing", "tools/check_gpu.sh missing")
    code, output = run([str(checker)])
    status = "ok" if code == 0 else "blocked"
    parts = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parts[key] = value
    detail = (
        f"{parts.get('gpu_name', 'unknown')} | "
        f"vram {parts.get('vram_used_mib', '?')}/{parts.get('vram_total_mib', '?')} MiB | "
        f"ceiling {parts.get('vram_hard_ceiling_mib', '?')} MiB | "
        f"{parts.get('gpu_status', status)}"
    )
    return Check("gpu", status, detail)


def comfy_check() -> Check:
    try:
        with urlopen(COMFY_URL, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return Check("comfyui", "missing", f"not reachable: {exc}")

    system = payload.get("system", {})
    devices = payload.get("devices", [])
    device = devices[0] if devices else {}
    detail = (
        f"version {system.get('comfyui_version', 'unknown')} | "
        f"{device.get('name', 'no cuda device')}"
    )
    return Check("comfyui", "ok", detail)


def github_check() -> Check:
    if not shutil.which("gh"):
        return Check("github", "missing", "gh not found")
    code, output = run(
        [
            "gh",
            "repo",
            "view",
            "--json",
            "nameWithOwner,url,pushedAt",
        ],
        timeout=10,
    )
    if code != 0:
        return Check("github", "warn", first_line(output) or "gh repo view failed")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return Check("github", "warn", first_line(output) or "gh repo view returned invalid JSON")
    detail = (
        f"repo={payload.get('nameWithOwner', 'unknown')} "
        f"url={payload.get('url', 'unknown')} "
        f"pushedAt={payload.get('pushedAt', 'unknown')}"
    )
    return Check("github", "ok", detail)


def python_environment_warnings() -> list[Check]:
    checks: list[Check] = []
    code, output = run(
        [
            sys.executable,
            "-c",
            "import numpy, torch; print(f'numpy={numpy.__version__} torch={torch.__version__}')",
        ],
        timeout=15,
    )
    if code == 0:
        status = "warn" if "Failed to initialize NumPy" in output or "NumPy 1.x" in output else "ok"
        checks.append(Check("python-torch-numpy", status, first_line(output)))
    else:
        checks.append(Check("python-torch-numpy", "warn", first_line(output) or output[:180]))
    return checks


def collect() -> dict[str, Any]:
    checks: list[Check] = []

    checks.extend(
        [
            command_check("python", "python3", ["--version"]),
            command_check("tesseract", "tesseract", ["--version"]),
            command_check("ffmpeg", "ffmpeg", ["-version"]),
            command_check("imagemagick", "magick", ["--version"]),
            command_check("exiftool", "exiftool", ["-ver"]),
            command_check("git", "git", ["--version"]),
            command_check("gh", "gh", ["--version"]),
            command_check("ollama", "ollama", ["--version"]),
        ]
    )

    checks.extend(
        [
            module_check("Pillow", "pillow"),
            module_check("opencv-python", "opencv-python"),
            module_check("numpy"),
            module_check("pandas"),
            module_check("pytesseract"),
            module_check("scikit-image"),
            module_check("torch"),
            module_check("transformers"),
            module_check("rembg"),
            module_check("onnxruntime"),
            module_check("diffusers"),
        ]
    )

    checks.extend(
        [
            file_check("opencv-enhance", ROOT / "tools" / "local_photo_enhance.py"),
            file_check("comfy-img2img", ROOT / "tools" / "comfy_photo_enhance.py"),
            file_check("comfy-upscale", ROOT / "tools" / "comfy_p54_upscale.py"),
            file_check("poster-router", ROOT / "tools" / "poster_route_decision.py"),
            file_check("poster-quality", ROOT / "tools" / "poster_quality_gate.py"),
            file_check("poster-batch", ROOT / "tools" / "local_poster_batch.py"),
            file_check("poster-workflow-doc", ROOT / "docs" / "local_poster_workflow.md"),
            file_check("comfy-photo-doc", ROOT / "docs" / "local_comfyui_photo_pipeline.md"),
        ]
    )

    checks.extend([gpu_check(), comfy_check(), github_check()])
    checks.extend(python_environment_warnings())

    return {
        "workspace": str(ROOT),
        "checks": [asdict(check) for check in checks],
        "summary": summarize(checks),
    }


def summarize(checks: list[Check]) -> dict[str, int]:
    counts = {"ok": 0, "warn": 0, "missing": 0, "blocked": 0}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    return counts


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Photo Capability Check",
        "",
        f"Workspace: `{snapshot['workspace']}`",
        "",
        "| Capability | Status | Detail |",
        "|---|---|---|",
    ]
    for item in snapshot["checks"]:
        lines.append(f"| `{item['name']}` | `{item['status']}` | {item['detail']} |")
    summary = snapshot["summary"]
    lines.extend(
        [
            "",
            f"Summary: ok={summary.get('ok', 0)} warn={summary.get('warn', 0)} "
            f"missing={summary.get('missing', 0)} blocked={summary.get('blocked', 0)}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local photo processing capabilities.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    snapshot = collect()
    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
