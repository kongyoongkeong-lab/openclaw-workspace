#!/usr/bin/env python3
"""Read-only local video generation capability checker for ComfyUI.

This script does not download models, start services, mutate ComfyUI, or queue
generation jobs. It reports whether the current local ComfyUI host can safely
attempt video generation under the workspace VRAM ceiling.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
COMFY_URL = "http://127.0.0.1:8188"
GPU_CHECK = ROOT / "tools" / "check_gpu.sh"
VRAM_CEILING_MIB = 9728

WORKFLOWS = {
    "wan22_t2v": {
        "label": "Wan 2.2 Text to Video",
        "blueprint": "/workspace/blueprints/Text to Video (Wan 2.2).json",
        "risk": "high",
        "required_nodes": ["CLIPLoader", "UNETLoader", "VAELoader", "WanVideoSampler"],
        "required_files": [
            {
                "name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "directory": "text_encoders",
                "container_path": "/workspace/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                "size_gib": 6.27,
            },
            {
                "name": "wan_2.1_vae.safetensors",
                "directory": "vae",
                "container_path": "/workspace/models/vae/wan_2.1_vae.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
                "size_gib": 0.24,
            },
            {
                "name": "wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
                "directory": "diffusion_models",
                "container_path": "/workspace/models/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
                "size_gib": 13.31,
            },
            {
                "name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                "directory": "diffusion_models",
                "container_path": "/workspace/models/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                "size_gib": 13.31,
            },
            {
                "name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                "directory": "loras",
                "container_path": "/workspace/models/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                "size_gib": 1.14,
            },
            {
                "name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
                "directory": "loras",
                "container_path": "/workspace/models/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
                "url": "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors",
                "size_gib": 1.14,
            },
        ],
        "notes": [
            "Large fp8 workflow; treat as unsafe until a tiny smoke profile is proven.",
            "Prefer low frame count and modest resolution if Jason explicitly approves a test later.",
        ],
    },
    "ltx23_t2v": {
        "label": "LTX 2.3 Text to Video",
        "blueprint": "/workspace/blueprints/Text to Video (LTX-2.3).json",
        "risk": "high",
        "required_nodes": ["LTXVConditioning", "LTXVScheduler", "KSampler", "SaveWEBM"],
        "required_files": [
            {
                "name": "ltx-2.3-22b-dev-fp8.safetensors",
                "directory": "checkpoints",
                "container_path": "/workspace/models/checkpoints/ltx-2.3-22b-dev-fp8.safetensors",
                "url": "https://huggingface.co/Lightricks/LTX-2.3-fp8/resolve/main/ltx-2.3-22b-dev-fp8.safetensors",
                "size_gib": 27.14,
            },
            {
                "name": "ltx-2.3-22b-distilled-lora-384.safetensors",
                "directory": "loras",
                "container_path": "/workspace/models/loras/ltx-2.3-22b-distilled-lora-384.safetensors",
                "url": "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors",
                "size_gib": 7.08,
            },
            {
                "name": "ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
                "directory": "latent_upscale_models",
                "container_path": "/workspace/models/latent_upscale_models/ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
                "url": "https://huggingface.co/Lightricks/LTX-2.3/resolve/main/ltx-2.3-spatial-upscaler-x2-1.1.safetensors",
                "size_gib": 0.93,
            },
            {
                "name": "gemma_3_12B_it_fp4_mixed.safetensors",
                "directory": "text_encoders",
                "container_path": "/workspace/models/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors",
                "url": "https://huggingface.co/Comfy-Org/ltx-2/resolve/main/split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors",
                "size_gib": 8.80,
            },
        ],
        "notes": [
            "Very large checkpoint set; likely not suitable for 9.5GB VRAM ceiling without a proven low-memory profile.",
            "Blueprint default is landscape API-style quality; phone output would still need normalization.",
        ],
    },
}


@dataclass
class Check:
    name: str
    status: str
    detail: str


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
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return result.returncode, output


def fetch_json(url: str, timeout: int = 5) -> tuple[dict[str, Any] | None, str]:
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), ""
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return None, str(exc)


def parse_gpu_output(output: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parts[key] = value
    return parts


def gpu_status() -> tuple[Check, dict[str, Any]]:
    if not GPU_CHECK.exists():
        return Check("gpu", "blocked", "tools/check_gpu.sh missing"), {}
    code, output = run([str(GPU_CHECK)])
    parts = parse_gpu_output(output)
    used = int(parts.get("vram_used_mib", "0") or 0)
    total = int(parts.get("vram_total_mib", "0") or 0)
    free = max(total - used, 0)
    ceiling = int(parts.get("vram_hard_ceiling_mib", VRAM_CEILING_MIB) or VRAM_CEILING_MIB)
    ok = code == 0 and used < ceiling
    detail = (
        f"{parts.get('gpu_name', 'unknown')} | used={used} MiB | "
        f"free={free} MiB | total={total} MiB | ceiling={ceiling} MiB"
    )
    return Check("gpu", "ok" if ok else "blocked", detail), {
        "name": parts.get("gpu_name", "unknown"),
        "used_mib": used,
        "free_mib": free,
        "total_mib": total,
        "ceiling_mib": ceiling,
        "raw_status": parts.get("gpu_status", ""),
    }


def comfy_status(server: str) -> tuple[Check, dict[str, Any]]:
    payload, error = fetch_json(f"{server}/system_stats")
    if payload is None:
        return Check("comfyui", "blocked", f"not reachable: {error}"), {}
    system = payload.get("system", {})
    devices = payload.get("devices", [])
    device = devices[0] if devices else {}
    detail = (
        f"version={system.get('comfyui_version', 'unknown')} | "
        f"python={system.get('python_version', 'unknown').split()[0]} | "
        f"device={device.get('name', 'none')}"
    )
    return Check("comfyui", "ok", detail), payload


def object_info(server: str) -> tuple[Check, dict[str, Any]]:
    payload, error = fetch_json(f"{server}/object_info")
    if payload is None:
        return Check("object_info", "blocked", f"not reachable: {error}"), {}
    video_hits = sum(1 for key in payload if "video" in key.lower())
    return Check("object_info", "ok", f"{len(payload)} nodes loaded; video-like nodes={video_hits}"), payload


def container_exists(name: str) -> bool:
    if not shutil.which("docker"):
        return False
    code, output = run(["docker", "ps", "--format", "{{.Names}}"], timeout=8)
    return code == 0 and name in output.splitlines()


def container_path_exists(container: str, path: str) -> bool:
    code, _ = run(["docker", "exec", container, "test", "-e", path], timeout=8)
    return code == 0


def local_path_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def path_exists(path: str, container: str | None) -> bool:
    if container:
        return container_path_exists(container, path)
    return local_path_exists(path)


def disk_free_gib(path: Path = ROOT) -> float:
    usage = shutil.disk_usage(path)
    return round(usage.free / 1024**3, 2)


def workflow_report(workflow_id: str, spec: dict[str, Any], object_nodes: dict[str, Any], container: str | None) -> dict[str, Any]:
    blueprint = spec["blueprint"]
    blueprint_present = path_exists(blueprint, container)
    required_files = []
    missing_size = 0.0
    for item in spec["required_files"]:
        present = path_exists(item["container_path"], container)
        if not present:
            missing_size += float(item["size_gib"])
        required_files.append({**item, "present": present})

    available_nodes = sorted(object_nodes)
    node_hits = {
        name: any(name.lower() in node.lower() for node in available_nodes)
        for name in spec.get("required_nodes", [])
    }
    node_ready = any(node_hits.values())
    files_ready = all(item["present"] for item in required_files)
    missing_count = sum(1 for item in required_files if not item["present"])

    if not blueprint_present:
        verdict = "blocked"
        reason = "blueprint missing"
    elif not node_ready:
        verdict = "blocked"
        reason = "required video nodes not detected"
    elif not files_ready:
        verdict = "blocked"
        reason = f"missing {missing_count} model file(s)"
    elif spec["risk"] == "high":
        verdict = "caution"
        reason = "files appear present, but workflow is high VRAM risk"
    else:
        verdict = "ready"
        reason = "required files and nodes present"

    return {
        "id": workflow_id,
        "label": spec["label"],
        "risk": spec["risk"],
        "verdict": verdict,
        "reason": reason,
        "blueprint": blueprint,
        "blueprint_present": blueprint_present,
        "node_hits": node_hits,
        "required_files": required_files,
        "missing_files": [item["name"] for item in required_files if not item["present"]],
        "missing_download_gib": round(missing_size, 2),
        "total_model_gib": round(sum(float(item["size_gib"]) for item in required_files), 2),
        "notes": spec["notes"],
    }


def summarize(workflows: list[dict[str, Any]], gpu: dict[str, Any], free_disk_gib: float) -> dict[str, Any]:
    any_ready = any(item["verdict"] in {"ready", "caution"} for item in workflows)
    total_missing = round(sum(float(item["missing_download_gib"]) for item in workflows), 2)
    blockers: list[str] = []
    warnings: list[str] = []

    if gpu and int(gpu.get("used_mib", 0)) >= int(gpu.get("ceiling_mib", VRAM_CEILING_MIB)):
        blockers.append("current VRAM usage exceeds safety ceiling")
    if not any_ready:
        blockers.append("no local video workflow has all required model files")
    if free_disk_gib < 80:
        warnings.append("disk headroom is low for video model downloads")
    warnings.append("Wan/LTX local video remains high VRAM risk on a 9.5GB operating ceiling")

    return {
        "local_video_ready": any_ready and not blockers,
        "recommended_next_action": (
            "download nothing; choose a specific workflow and approve model setup"
            if blockers
            else "run a tiny guarded smoke test before full phone-video generation"
        ),
        "blockers": blockers,
        "warnings": warnings,
        "total_missing_download_gib_across_known_workflows": total_missing,
        "disk_free_gib": free_disk_gib,
    }


def collect(args: argparse.Namespace) -> dict[str, Any]:
    checks: list[Check] = []

    gpu_check, gpu = gpu_status()
    checks.append(gpu_check)

    comfy_check, comfy_payload = comfy_status(args.server.rstrip("/"))
    checks.append(comfy_check)

    object_check, nodes = object_info(args.server.rstrip("/"))
    checks.append(object_check)

    container = args.container if args.container and container_exists(args.container) else None
    if args.container and not container:
        checks.append(Check("container", "warn", f"{args.container} not found; falling back to host path checks"))
    elif container:
        checks.append(Check("container", "ok", container))

    free_disk = disk_free_gib()
    checks.append(Check("disk", "ok" if free_disk >= 80 else "warn", f"{free_disk} GiB free at {ROOT}"))

    workflows = [
        workflow_report(workflow_id, spec, nodes, container)
        for workflow_id, spec in WORKFLOWS.items()
    ]

    return {
        "workspace": str(ROOT),
        "server": args.server.rstrip("/"),
        "container": container,
        "checks": [asdict(check) for check in checks],
        "gpu": gpu,
        "comfyui": {
            "system": comfy_payload.get("system", {}) if comfy_payload else {},
            "devices": comfy_payload.get("devices", []) if comfy_payload else [],
        },
        "workflows": workflows,
        "summary": summarize(workflows, gpu, free_disk),
    }


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("local_video_ready:", summary["local_video_ready"])
    print("recommended_next_action:", summary["recommended_next_action"])
    print()
    print("checks:")
    for check in report["checks"]:
        print(f"- {check['name']}: {check['status']} | {check['detail']}")
    print()
    print("workflows:")
    for workflow in report["workflows"]:
        print(
            f"- {workflow['id']}: {workflow['verdict']} | "
            f"{workflow['label']} | missing={workflow['missing_download_gib']} GiB | "
            f"{workflow['reason']}"
        )
        if workflow["missing_files"]:
            for missing in workflow["missing_files"]:
                print(f"  missing: {missing}")
    print()
    if summary["blockers"]:
        print("blockers:")
        for item in summary["blockers"]:
            print(f"- {item}")
    if summary["warnings"]:
        print("warnings:")
        for item in summary["warnings"]:
            print(f"- {item}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only local ComfyUI video capability checker.")
    parser.add_argument("--server", default=COMFY_URL)
    parser.add_argument("--container", default="pentagon-comfyui")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = collect(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
