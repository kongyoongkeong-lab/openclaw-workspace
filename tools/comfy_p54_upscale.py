#!/usr/bin/env python3
"""Run the P5.4 local ComfyUI upscale pass through the API."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any

import requests
from PIL import Image


def upload_image(server: str, image_path: Path) -> str:
    with image_path.open("rb") as handle:
        files = {"image": (image_path.name, handle, "image/jpeg")}
        response = requests.post(f"{server}/upload/image", files=files, data={"overwrite": "true"}, timeout=60)
    response.raise_for_status()
    return response.json()["name"]


def queue_prompt(server: str, prompt: dict[str, Any], client_id: str) -> str:
    response = requests.post(f"{server}/prompt", json={"prompt": prompt, "client_id": client_id}, timeout=30)
    response.raise_for_status()
    return response.json()["prompt_id"]


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
        time.sleep(0.8)
    raise TimeoutError(f"Timed out waiting for ComfyUI prompt {prompt_id}. Last status: {last_status}")


def download_image(server: str, image_ref: dict[str, str], output_path: Path, max_edge: int) -> None:
    response = requests.get(f"{server}/view", params=image_ref, timeout=180)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)

    if max_edge > 0:
        with Image.open(output_path) as image:
            image.load()
            largest = max(image.size)
            if largest > max_edge:
                scale = max_edge / largest
                resized = image.resize(
                    (round(image.width * scale), round(image.height * scale)),
                    Image.Resampling.LANCZOS,
                )
                resized.save(output_path)


def build_upscale_prompt(image_name: str, upscale_model: str, filename_prefix: str) -> dict[str, Any]:
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name},
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": {"model_name": upscale_model},
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": {"image": ["1", 0], "upscale_model": ["2", 0]},
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {"images": ["3", 0], "filename_prefix": filename_prefix},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local P5.4 ComfyUI RealESRGAN upscale.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--upscale-model", default="RealESRGAN_x4plus.pth")
    parser.add_argument("--max-edge", type=int, default=2600)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    server = args.server.rstrip("/")
    client_id = str(uuid.uuid4())
    image_name = upload_image(server, args.image)
    prompt = build_upscale_prompt(
        image_name=image_name,
        upscale_model=args.upscale_model,
        filename_prefix="openclaw_p54_upscale",
    )
    prompt_id = queue_prompt(server, prompt, client_id)
    image_ref = wait_for_output(server, prompt_id, args.timeout)
    download_image(server, image_ref, args.output, args.max_edge)
    print(args.output)
    print(f"prompt_id={prompt_id} image={image_ref['filename']} upscale_model={args.upscale_model}")


if __name__ == "__main__":
    main()
