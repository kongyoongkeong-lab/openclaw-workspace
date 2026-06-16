#!/usr/bin/env python3
"""Safe Hugging Face model download helper for OpenClaw.

The helper validates account/model access and disk capacity before invoking
`hf download`. Without --yes it is a dry-run planner. It never prints token material.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_DIR = Path("/mnt/d/models/huggingface")
MANIFEST_NAME = "openclaw_hf_download_manifest.json"
MIN_FREE_GIB_AFTER_DOWNLOAD = 10
TOKEN_ENV_NAMES = (
    "HF_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_TOKEN",
)
TOKEN_PATHS = (
    Path.home() / ".cache" / "huggingface" / "token",
    Path.home() / ".huggingface" / "token",
)
ENV_PATH = Path.home() / ".openclaw" / ".env"


@dataclass(frozen=True)
class TokenCandidate:
    label: str
    source: str
    token: str


@dataclass(frozen=True)
class ModelPlan:
    model_id: str
    target_dir: Path
    file_count: int
    known_bytes: int
    unknown_size_count: int
    gated: bool
    private: bool
    sha: str | None


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def discover_token() -> TokenCandidate | None:
    env_file = load_env_file(ENV_PATH)
    for source_name, mapping in (("env", os.environ), ("~/.openclaw/.env", env_file)):
        for name in TOKEN_ENV_NAMES:
            value = mapping.get(name, "").strip()
            if value:
                return TokenCandidate(label=name, source=source_name, token=value)
    for path in TOKEN_PATHS:
        if not path.exists():
            continue
        value = path.read_text(encoding="utf-8", errors="ignore").strip()
        if value:
            return TokenCandidate(label=path.name, source=str(path), token=value)
    return None


def run_command(args: list[str], timeout: int, env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            args,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            env=env,
        )
    except FileNotFoundError:
        return 127, "missing"
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    return completed.returncode, completed.stdout.strip()


def human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def safe_model_dir_name(model_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "__", model_id.strip())
    return normalized.strip("._-") or "model"


def resolve_target_dir(model_id: str, base_dir: Path, local_dir: str | None) -> Path:
    if local_dir:
        return Path(local_dir).expanduser().resolve()
    return (base_dir / safe_model_dir_name(model_id)).resolve()


def get_model_plan(model_id: str, target_dir: Path, token: TokenCandidate | None) -> ModelPlan:
    try:
        from huggingface_hub import HfApi  # type: ignore
    except Exception as exc:
        raise RuntimeError("huggingface_hub package is missing") from exc

    api = HfApi(token=token.token if token else None)
    try:
        info = api.model_info(model_id, files_metadata=True)
    except Exception as exc:
        lowered = str(exc).lower()
        if "gated" in lowered or "401" in lowered or "403" in lowered:
            raise RuntimeError("model requires token or Hugging Face access approval") from exc
        if "404" in lowered or "not found" in lowered:
            raise RuntimeError("model not found, private, or unavailable to this account") from exc
        raise RuntimeError(f"model metadata probe failed: {type(exc).__name__}") from exc

    known_bytes = 0
    unknown_size_count = 0
    siblings = getattr(info, "siblings", None) or []
    for sibling in siblings:
        size = getattr(sibling, "size", None)
        if isinstance(size, int) and size >= 0:
            known_bytes += size
        else:
            unknown_size_count += 1

    return ModelPlan(
        model_id=getattr(info, "modelId", model_id),
        target_dir=target_dir,
        file_count=len(siblings),
        known_bytes=known_bytes,
        unknown_size_count=unknown_size_count,
        gated=bool(getattr(info, "gated", False)),
        private=bool(getattr(info, "private", False)),
        sha=getattr(info, "sha", None),
    )


def ensure_disk_capacity(plan: ModelPlan, reserve_gib: int) -> tuple[bool, str]:
    base = plan.target_dir.parent
    base.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(base)
    reserve_bytes = reserve_gib * 1024**3
    if plan.known_bytes <= 0:
        return True, f"free={human_bytes(usage.free)} estimate=unknown reserve={reserve_gib} GiB"
    remaining = usage.free - plan.known_bytes
    ok = remaining >= reserve_bytes
    return ok, (
        f"free={human_bytes(usage.free)} estimate={human_bytes(plan.known_bytes)} "
        f"post_download={human_bytes(max(0, remaining))} reserve={reserve_gib} GiB"
    )


def existing_target_summary(target_dir: Path) -> str:
    if not target_dir.exists():
        return "absent"
    files = [path for path in target_dir.rglob("*") if path.is_file()]
    return f"exists files={len(files)}"


def write_manifest(plan: ModelPlan, token: TokenCandidate | None) -> None:
    payload: dict[str, Any] = {
        "schema": "openclaw.huggingface_download_manifest.v1",
        "model_id": plan.model_id,
        "target_dir": str(plan.target_dir),
        "file_count": plan.file_count,
        "known_bytes": plan.known_bytes,
        "unknown_size_count": plan.unknown_size_count,
        "gated": plan.gated,
        "private": plan.private,
        "sha": plan.sha,
        "token_source": token.source if token else None,
        "downloaded_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "secret_policy": "token material is never stored here",
    }
    (plan.target_dir / MANIFEST_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_download_command(plan: ModelPlan, revision: str | None) -> list[str]:
    hf_bin = shutil.which("hf") or shutil.which("huggingface-cli")
    if not hf_bin:
        raise RuntimeError("hf CLI is missing")
    command = [hf_bin, "download", plan.model_id, "--local-dir", str(plan.target_dir)]
    if revision:
        command.extend(["--revision", revision])
    return command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_id", nargs="?", help="Hugging Face model ID, for example Qwen/Qwen2.5-0.5B-Instruct.")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR), help=f"Base model directory. Default: {DEFAULT_BASE_DIR}")
    parser.add_argument("--local-dir", help="Exact target directory. Overrides --base-dir.")
    parser.add_argument("--revision", help="Optional branch, tag, or commit revision.")
    parser.add_argument("--reserve-gib", type=int, default=MIN_FREE_GIB_AFTER_DOWNLOAD)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--yes", action="store_true", help="Actually download. Without this flag the helper only prints a plan.")
    parser.add_argument("--force", action="store_true", help="Allow downloading into an existing non-empty target directory.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic path planning self-test.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        assert safe_model_dir_name("Qwen/Qwen2.5-0.5B-Instruct") == "Qwen__Qwen2.5-0.5B-Instruct"
        print("PASS: Hugging Face download self-test passed.")
        return 0
    if not args.model_id:
        raise SystemExit("model_id is required unless --self-test is used")
    token = discover_token()
    target_dir = resolve_target_dir(args.model_id, Path(args.base_dir).expanduser(), args.local_dir)

    print("Hugging Face download planner")
    print(f"model: {args.model_id}")
    print(f"target: {target_dir}")
    print("secret policy: token fields are never printed")
    print(f"token: {'discovered' if token else 'not discovered'}")

    try:
        plan = get_model_plan(args.model_id, target_dir, token)
    except RuntimeError as exc:
        print(f"model access: failed ({exc})")
        return 2

    disk_ok, disk_message = ensure_disk_capacity(plan, args.reserve_gib)
    target_summary = existing_target_summary(target_dir)

    print(f"model access: ok model={plan.model_id}")
    print(f"files: {plan.file_count}")
    print(f"known size: {human_bytes(plan.known_bytes)}")
    print(f"unknown file sizes: {plan.unknown_size_count}")
    print(f"gated: {str(plan.gated).lower()}")
    print(f"private: {str(plan.private).lower()}")
    print(f"revision sha: {plan.sha or 'unknown'}")
    print(f"disk: {'ok' if disk_ok else 'blocked'} {disk_message}")
    print(f"target state: {target_summary}")

    if not disk_ok:
        return 3
    if target_dir.exists() and any(target_dir.iterdir()) and not args.force:
        print("download: blocked because target exists; pass --force to resume/update this directory")
        return 4
    if not args.yes:
        print("download: plan only; pass --yes to start")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if token:
        env["HF_TOKEN"] = token.token

    try:
        command = build_download_command(plan, args.revision)
    except RuntimeError as exc:
        print(f"download: failed ({exc})")
        return 2

    print("download: starting")
    code, output = run_command(command, timeout=args.timeout, env=env)
    if code != 0:
        lowered = output.lower()
        if "401" in lowered or "403" in lowered or "gated" in lowered:
            print("download: failed (requires Hugging Face access approval or valid token)")
        else:
            print(f"download: failed exit={code}")
        return code or 1

    write_manifest(plan, token)
    print("download: complete")
    print(f"manifest: {plan.target_dir / MANIFEST_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
