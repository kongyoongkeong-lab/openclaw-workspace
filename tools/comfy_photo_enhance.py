#!/usr/bin/env python3
"""Run a conservative ComfyUI img2img enhancement through the local API."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any

import requests


DEFAULT_POSITIVE = (
    "realistic documentary food stall photo, natural skin tone, clean light, "
    "preserve identity, preserve original scene, gentle contrast, detailed steam, "
    "authentic local shop atmosphere"
)
DEFAULT_NEGATIVE = (
    "cartoon, illustration, plastic skin, overprocessed, oversaturated, deformed face, "
    "changed identity, extra fingers, bad hands, blurry, text, watermark, low quality"
)


def upload_image(server: str, image_path: Path) -> str:
    with image_path.open("rb") as handle:
        files = {"image": (image_path.name, handle, "image/jpeg")}
        response = requests.post(f"{server}/upload/image", files=files, data={"overwrite": "true"}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    return payload["name"]


def queue_prompt(server: str, prompt: dict[str, Any], client_id: str) -> str:
    response = requests.post(
        f"{server}/prompt",
        json={"prompt": prompt, "client_id": client_id},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["prompt_id"]


def wait_for_output(server: str, prompt_id: str, timeout_s: int) -> dict[str, str]:
    deadline = time.time() + timeout_s
    last_status = ""
    while time.time() < deadline:
        response = requests.get(f"{server}/history/{prompt_id}", timeout=30)
        response.raise_for_status()
        history = response.json()
        item = history.get(prompt_id)
        if item:
            status = item.get("status", {})
            last_status = json.dumps(status, ensure_ascii=False)
            outputs = item.get("outputs", {})
            for node_output in outputs.values():
                for image in node_output.get("images", []):
                    return {
                        "filename": image["filename"],
                        "subfolder": image.get("subfolder", ""),
                        "type": image.get("type", "output"),
                    }
            if status.get("completed"):
                raise RuntimeError(f"Prompt completed without image output: {last_status}")
        time.sleep(1.0)
    raise TimeoutError(f"Timed out waiting for ComfyUI prompt {prompt_id}. Last status: {last_status}")


def download_image(server: str, image_ref: dict[str, str], output_path: Path) -> None:
    response = requests.get(f"{server}/view", params=image_ref, timeout=120)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)


def build_img2img_prompt(
    image_name: str,
    checkpoint: str,
    positive: str,
    negative: str,
    denoise: float,
    steps: int,
    cfg: float,
    seed: int,
    filename_prefix: str,
) -> dict[str, Any]:
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["1", 1]},
        },
        "4": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        "5": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["4", 0], "vae": ["1", 2]},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": denoise,
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": filename_prefix},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local ComfyUI SDXL img2img photo enhancement.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--checkpoint", default="sd_xl_base_1.0.safetensors")
    parser.add_argument("--positive", default=DEFAULT_POSITIVE)
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE)
    parser.add_argument("--denoise", type=float, default=0.16)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--cfg", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=20260523)
    parser.add_argument("--timeout", type=int, default=360)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    server = args.server.rstrip("/")
    client_id = str(uuid.uuid4())
    image_name = upload_image(server, args.image)
    prompt = build_img2img_prompt(
        image_name=image_name,
        checkpoint=args.checkpoint,
        positive=args.positive,
        negative=args.negative,
        denoise=max(0.0, min(args.denoise, 1.0)),
        steps=max(1, args.steps),
        cfg=max(0.0, args.cfg),
        seed=max(0, args.seed),
        filename_prefix="openclaw_photo_enhance",
    )
    prompt_id = queue_prompt(server, prompt, client_id)
    image_ref = wait_for_output(server, prompt_id, args.timeout)
    download_image(server, image_ref, args.output)
    print(args.output)
    print(f"prompt_id={prompt_id} image={image_ref['filename']} denoise={args.denoise} steps={args.steps} cfg={args.cfg}")


if __name__ == "__main__":
    main()
