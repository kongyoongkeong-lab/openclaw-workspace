#!/usr/bin/env python3
"""Check Hugging Face CLI/token readiness without printing token material."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "huggingface_state.json"
ENV_PATH = Path.home() / ".openclaw" / ".env"
TOKEN_PATHS = (
    Path.home() / ".cache" / "huggingface" / "token",
    Path.home() / ".huggingface" / "token",
)
TOKEN_ENV_NAMES = (
    "HF_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "HUGGING_FACE_HUB_TOKEN",
    "HUGGINGFACE_TOKEN",
)


@dataclass(frozen=True)
class TokenCandidate:
    label: str
    source: str
    token: str


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


def add_candidate(candidates: list[TokenCandidate], seen: set[str], label: str, source: str, value: str) -> None:
    token = value.strip()
    if not token or token in seen:
        return
    seen.add(token)
    candidates.append(TokenCandidate(label=label, source=source, token=token))


def discover_tokens() -> list[TokenCandidate]:
    candidates: list[TokenCandidate] = []
    seen: set[str] = set()
    env_file = load_env_file(ENV_PATH)
    for source_name, mapping in (("env", os.environ), ("~/.openclaw/.env", env_file)):
        for name in TOKEN_ENV_NAMES:
            value = mapping.get(name)
            if value:
                add_candidate(candidates, seen, name, source_name, value)
    for path in TOKEN_PATHS:
        if path.exists():
            add_candidate(candidates, seen, path.name, str(path), path.read_text(encoding="utf-8", errors="ignore"))
    return candidates


def package_version() -> str:
    try:
        import huggingface_hub  # type: ignore
    except Exception:
        return "missing"
    return getattr(huggingface_hub, "__version__", "unknown")


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
    output = completed.stdout.strip()
    return completed.returncode, output


def hf_whoami(candidate: TokenCandidate, timeout: int) -> str:
    hf_bin = shutil.which("hf") or shutil.which("huggingface-cli")
    if not hf_bin:
        return hub_whoami(candidate)
    env = os.environ.copy()
    env["HF_TOKEN"] = candidate.token
    command = [hf_bin, "auth", "whoami"] if Path(hf_bin).name == "hf" else [hf_bin, "whoami"]
    code, output = run_command(command, timeout=timeout, env=env)
    if code != 0:
        lowered = output.lower()
        if "invalid" in lowered or "unauthorized" in lowered or "401" in lowered:
            return "invalid_or_unauthorized"
        hub_status = hub_whoami(candidate)
        return hub_status if hub_status.startswith("ok ") else f"error_exit_{code}"
    first_line = output.splitlines()[0].strip() if output else "ok"
    if first_line.lower().startswith("user:"):
        first_line = first_line.split(":", 1)[1].strip()
    return f"ok user={first_line}"


def hub_whoami(candidate: TokenCandidate) -> str:
    try:
        from huggingface_hub import HfApi  # type: ignore

        info = HfApi(token=candidate.token).whoami()
    except Exception as exc:
        lowered = str(exc).lower()
        if "invalid" in lowered or "unauthorized" in lowered or "401" in lowered:
            return "invalid_or_unauthorized"
        return "hub_whoami_error"
    return f"ok user={info.get('name') or info.get('fullname') or 'unknown'}"


def check_model_access(model_id: str, candidate: TokenCandidate | None, timeout: int) -> str:
    script = (
        "from huggingface_hub import model_info\n"
        "import os, sys\n"
        "model = sys.argv[1]\n"
        "token = os.environ.get('HF_TOKEN') or None\n"
        "info = model_info(model, token=token, timeout=20)\n"
        "print(getattr(info, 'modelId', model))\n"
    )
    env = os.environ.copy()
    if candidate:
        env["HF_TOKEN"] = candidate.token
    code, output = run_command(["python3", "-c", script, model_id], timeout=timeout, env=env)
    if code == 0:
        return f"ok model={output.splitlines()[0] if output else model_id}"
    lowered = output.lower()
    if "gated" in lowered or "401" in lowered or "403" in lowered:
        return "requires_token_or_access_approval"
    if "not found" in lowered or "404" in lowered:
        return "model_not_found_or_private"
    return f"error_exit_{code}"


def save_state(selected: TokenCandidate | None, status: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "openclaw.huggingface_state.v1",
        "selected_label": selected.label if selected else None,
        "selected_source": selected.source if selected else None,
        "status": status,
        "updated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "secret_policy": "token material is never stored here",
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-only", action="store_true", help="List local readiness without network/account probes.")
    parser.add_argument("--whoami", action="store_true", help="Probe discovered tokens with Hugging Face account auth.")
    parser.add_argument("--model", help="Optional model ID to check with huggingface_hub.model_info.")
    parser.add_argument("--no-write", action="store_true", help="Do not update config/huggingface_state.json.")
    parser.add_argument("--timeout", type=int, default=30)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    hf_bin = shutil.which("hf")
    legacy_bin = shutil.which("huggingface-cli")
    candidates = discover_tokens()

    print("Hugging Face preflight")
    print(f"hf CLI: `{hf_bin or 'missing'}`")
    print(f"huggingface-cli: `{legacy_bin or 'missing'}`")
    print(f"huggingface_hub: `{package_version()}`")
    print("Secret policy: token fields are never printed.")

    print("\n| Token Label | Source | Status |")
    print("|---|---|---|")
    token_statuses: list[str] = []
    if not candidates:
        print("| none | environment/cache | missing |")
    else:
        for candidate in candidates:
            status = "discovered"
            if args.whoami:
                status = hf_whoami(candidate, args.timeout)
            token_statuses.append(status)
            print(f"| `{candidate.label}` | `{candidate.source}` | {status} |")

    selected = candidates[0] if candidates else None
    selected_status = "token_missing" if selected is None else "token_discovered"
    if token_statuses:
        selected_status = token_statuses[0]

    if args.model:
        model_status = check_model_access(args.model, selected, args.timeout)
        print(f"\nModel access `{args.model}`: {model_status}")
        selected_status = model_status

    if not args.list_only and not args.no_write:
        save_state(selected, selected_status)
        print(f"\nState file: `{STATE_FILE}`")

    if not hf_bin and not legacy_bin:
        print("\nNext step: install `huggingface_hub[cli]` in the active Python environment.")
        return 2
    if not candidates:
        print("\nNext step: create a Hugging Face access token, then set `HF_TOKEN` in `~/.openclaw/.env` or run `hf auth login`.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
