#!/usr/bin/env python3
"""Print a safe status snapshot for OpenClaw hybrid model routing."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "model_runtime.json"
GPU_CHECK = ROOT / "tools" / "check_gpu.sh"


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
    if not STATE_FILE.exists():
        return {"active_mode": "unknown", "error": f"missing {STATE_FILE}"}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def gpu_status() -> str:
    if GPU_CHECK.exists() and GPU_CHECK.is_file():
        code, output = run([str(GPU_CHECK)])
        return output if code == 0 else f"gpu_check_failed={output}"
    if shutil.which("nvidia-smi"):
        code, output = run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                "--format=csv,noheader",
            ]
        )
        return output if code == 0 else f"nvidia_smi_failed={output}"
    return "gpu_status=unavailable"


def ollama_status() -> str:
    if not shutil.which("ollama"):
        return "ollama=missing"
    code, output = run(["ollama", "list"])
    return output if code == 0 else f"ollama_list_failed={output}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print config state only; skip live GPU and Ollama probes.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic parser self-test.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        assert isinstance(load_state(), dict)
        print("PASS: model runtime status self-test passed.")
        return 0
    state = load_state()
    hardware = state.get("hardware", {})
    context = state.get("context_management", {})
    fallback = state.get("fallback_policy", {})
    ollama = state.get("providers", {}).get("ollama", {})
    models = ollama.get("models", {})

    print("OpenClaw model runtime")
    print(f"active_mode={state.get('active_mode', 'unknown')}")
    print(f"default_mode={state.get('default_mode', 'unknown')}")
    print(f"vram_hard_ceiling_mib={hardware.get('vram_hard_ceiling_mib', 'unknown')}")
    print(f"context_policy={context.get('policy', 'unknown')}")
    print(f"context_compression_trigger_ratio={context.get('compression_trigger_ratio', 'unknown')}")
    print(f"context_hard_stop_ratio={context.get('hard_stop_ratio', 'unknown')}")
    api_fallback = fallback.get("api_unavailable", {})
    print(f"api_unavailable_primary_fallback={api_fallback.get('primary', 'unknown')}")
    print(f"ollama_base_url={ollama.get('base_url', 'unknown')}")
    for role, model in models.items():
        print(f"model.{role}={model}")
    if args.dry_run:
        print("\nmode=dry-run, live GPU and Ollama probes skipped")
    else:
        print("\nGPU")
        print(gpu_status())
        print("\nOllama")
        print(ollama_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
