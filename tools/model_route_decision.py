#!/usr/bin/env python3
"""Recommend API/local routing with context and fallback safeguards."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "model_runtime.json"
GPU_CHECK = ROOT / "tools" / "check_gpu.sh"

LOCAL_FRIENDLY_TASKS = {
    "compact-reasoning",
    "classification",
    "summarization",
    "embedding",
    "private",
    "local-file",
}

API_FRIENDLY_TASKS = {
    "long-context",
    "tool-heavy",
    "codebase-wide",
    "current-knowledge",
    "multi-agent",
    "synthesis",
}


def run(command: list[str], timeout: int = 10) -> tuple[int, str]:
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
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return result.returncode, output.strip()


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def ollama_available() -> bool:
    return bool(shutil.which("ollama")) and run(["ollama", "list"])[0] == 0


def gpu_available() -> bool:
    if GPU_CHECK.exists() and GPU_CHECK.is_file():
        return run([str(GPU_CHECK)])[0] == 0
    return bool(shutil.which("nvidia-smi")) and run(["nvidia-smi", "-L"])[0] == 0


def choose_route(args: argparse.Namespace, state: dict) -> tuple[str, list[str], list[str]]:
    mode = args.mode or state.get("active_mode", "hybrid")
    task_type = args.task_type
    reasons: list[str] = [f"mode={mode}", f"task_type={task_type}"]
    warnings: list[str] = []

    context_policy = state.get("context_management", {})
    compression_trigger = float(context_policy.get("compression_trigger_ratio", 0.5))
    hard_stop = float(context_policy.get("hard_stop_ratio", 0.8))

    if args.context_ratio >= hard_stop:
        warnings.append("context_hard_stop: write handoff summary and reload minimal files")
    elif args.context_ratio >= compression_trigger:
        warnings.append("context_compression: summarize/offload before continuing")

    has_local = ollama_available() and gpu_available()
    reasons.append(f"local_available={str(has_local).lower()}")
    reasons.append(f"api_available={str(args.api_available).lower()}")

    if not args.api_available and has_local:
        return "local", reasons + ["api_unavailable_fallback"], warnings
    if not args.api_available and not has_local:
        return "blocked", reasons + ["api_and_local_unavailable"], warnings

    if mode == "api":
        return "api", reasons + ["api_first_mode"], warnings
    if mode == "local":
        if has_local:
            return "local", reasons + ["local_first_mode"], warnings
        return "api", reasons + ["local_unavailable_api_fallback"], warnings

    if task_type in API_FRIENDLY_TASKS:
        return "api", reasons + ["api_suited_task"], warnings
    if task_type in LOCAL_FRIENDLY_TASKS and has_local and args.context_ratio < hard_stop:
        return "local", reasons + ["local_suited_task"], warnings
    return "api", reasons + ["hybrid_default_orchestrator"], warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task-type",
        default="synthesis",
        choices=sorted(API_FRIENDLY_TASKS | LOCAL_FRIENDLY_TASKS),
    )
    parser.add_argument("--mode", choices=["api", "local", "hybrid"])
    parser.add_argument("--context-ratio", type=float, default=0.0)
    parser.add_argument("--api-available", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic routing self-test.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        state = {"active_mode": "api", "context_management": {"compression_trigger_ratio": 0.5, "hard_stop_ratio": 0.8}}
        test_args = argparse.Namespace(mode=None, task_type="long-context", context_ratio=0.0, api_available=True)
        route, reasons, warnings = choose_route(test_args, state)
        assert route == "api"
        assert "api_first_mode" in reasons
        assert warnings == []
        print("PASS: model route decision self-test passed.")
        return 0
    state = load_state()
    route, reasons, warnings = choose_route(args, state)
    payload = {"route": route, "reasons": reasons, "warnings": warnings}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"route={route}")
        for reason in reasons:
            print(f"reason={reason}")
        for warning in warnings:
            print(f"warning={warning}")
    return 2 if route == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
