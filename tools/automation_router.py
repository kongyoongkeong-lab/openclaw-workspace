#!/usr/bin/env python3
"""Local automation router for OpenClaw.

The router keeps browser, Windows UI Automation, and keyboard/mouse fallback
commands behind a small, auditable CLI. It is designed to run from WSL and call
Windows PowerShell through an explicit path.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PS = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
NODE = "node"


def run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def emit(proc: subprocess.CompletedProcess[str]) -> int:
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


def ps_file(script: str, *args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    if not PS.exists():
        return subprocess.CompletedProcess(
            args=[str(PS)],
            returncode=127,
            stdout="",
            stderr=f"PowerShell not found at {PS}",
        )
    return run(
        [
            str(PS),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / script),
            *args,
        ],
        timeout=timeout,
    )


def ps_command(command: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    if not PS.exists():
        return subprocess.CompletedProcess(
            args=[str(PS)],
            returncode=127,
            stdout="",
            stderr=f"PowerShell not found at {PS}",
        )
    return run(
        [str(PS), "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        timeout=timeout,
    )


def windows_path(path: Path) -> str:
    proc = run(["wslpath", "-w", str(path)], timeout=10)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return r"\\wsl.localhost\Ubuntu-22.04" + str(path).replace("/", "\\")


def status() -> dict[str, Any]:
    checks: dict[str, Any] = {
        "workspace": str(ROOT),
        "powershell_path": str(PS),
        "powershell_exists": PS.exists(),
    }

    proc = ps_command(
        "$ErrorActionPreference='Continue'; "
        "[PSCustomObject]@{"
        "Winget=(Get-Command winget -ErrorAction SilentlyContinue).Source;"
        "Py=(Get-Command py -ErrorAction SilentlyContinue).Source;"
        "Python=(Get-Command python -ErrorAction SilentlyContinue).Source;"
        "AutoHotkey=(Get-Command autohotkey -ErrorAction SilentlyContinue).Source;"
        "AutoHotkey64=(Get-Command 'C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe' -ErrorAction SilentlyContinue).Source;"
        "AutoHotkey64User=(Get-Command \"$env:LOCALAPPDATA\\Programs\\AutoHotkey\\v2\\AutoHotkey64.exe\" -ErrorAction SilentlyContinue).Source;"
        "FlaUInspect=(Get-Command FlaUInspect -ErrorAction SilentlyContinue).Source"
        "} | ConvertTo-Json -Compress"
    )
    checks["windows_tools_rc"] = proc.returncode
    if proc.stdout.strip():
        try:
            checks["windows_tools"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            checks["windows_tools_raw"] = proc.stdout.strip()
    if proc.stderr.strip():
        checks["windows_tools_stderr"] = proc.stderr.strip()

    cdp = ps_file("tools/chrome_cdp_bootstrap.ps1", "-StatusOnly", timeout=20)
    checks["cdp_status_rc"] = cdp.returncode
    if cdp.stdout.strip():
        try:
            checks["cdp_status"] = json.loads(cdp.stdout)
        except json.JSONDecodeError:
            checks["cdp_status_raw"] = cdp.stdout.strip()
    if cdp.stderr.strip():
        checks["cdp_status_stderr"] = cdp.stderr.strip()
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenClaw local automation router.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")
    sub.add_parser("cdp-status")
    sub.add_parser("cdp-restart")
    sub.add_parser("browser-smoke")

    win = sub.add_parser("windows")
    win.add_argument("action", choices=["list", "focus", "inspect", "screenshot"])
    win.add_argument("--match", default="Chrome|Doubao|豆包|Gemini")
    win.add_argument("--process", default="")
    win.add_argument("--max-depth", type=int, default=4)
    win.add_argument("--limit", type=int, default=220)
    win.add_argument("--output", default=r"C:\Users\jason\OpenClaw\captures\screen.png")

    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "cdp-status":
        return emit(ps_file("tools/chrome_cdp_bootstrap.ps1", "-StatusOnly", timeout=20))
    if args.command == "cdp-restart":
        return emit(ps_file("tools/chrome_cdp_bootstrap.ps1", "-RestartChrome", timeout=45))
    if args.command == "browser-smoke":
        script = windows_path(ROOT / "tools/playwright_cdp_smoke_windows.mjs")
        command = (
            "$ErrorActionPreference='Stop'; "
            "Set-Location 'C:\\Users\\jason\\OpenClaw\\automation-node'; "
            f"node '{script}'"
        )
        return emit(ps_command(command, timeout=35))
    if args.command == "windows":
        if args.action == "list":
            return emit(ps_file("tools/windows_ui/window_list.ps1", "-Match", args.match, timeout=30))
        if args.action == "focus":
            return emit(ps_file("tools/windows_ui/focus_window.ps1", "-Match", args.match, timeout=30))
        if args.action == "inspect":
            return emit(
                ps_file(
                    "tools/windows_ui/inspect_uia.ps1",
                    "-Match",
                    args.match,
                    "-MaxDepth",
                    str(args.max_depth),
                    "-Limit",
                    str(args.limit),
                    "-TargetProcessName",
                    args.process,
                    timeout=45,
                )
            )
        if args.action == "screenshot":
            return emit(ps_file("tools/windows_ui/screenshot.ps1", "-Output", args.output, timeout=30))
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
