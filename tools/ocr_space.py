#!/usr/bin/env python3
"""
ocr_space.py — Read text from screenshots using OCR.Space free API.
Use when image models are unavailable (OpenAI text-only, Google capped).

Usage:
  python3 tools/ocr_space.py <image_path> [--lang chs|eng|...]
"""
import argparse
import json
import os
import subprocess
import sys


def ocr_image(image_path: str, lang: str = "chs") -> dict:
    """Send image to OCR.Space via curl and return parsed JSON."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    file_size = os.path.getsize(image_path)
    if file_size > 5 * 1024 * 1024:
        raise ValueError(f"File too large: {file_size} bytes (max 5 MB)")

    cmd = [
        "curl", "-s",
        "-H", "apikey: helloworld",
        "-F", f"file=@{image_path}",
        "-F", f"language={lang}",
        "-F", "isOverlayRequired=false",
        "-F", "detectOrientation=true",
        "-F", "scale=true",
        "https://api.ocr.space/parse/image"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {result.stdout[:500]}")


def format_result(result: dict) -> str:
    """Format OCR result as plain text."""
    if result.get("IsErroredOnProcessing"):
        return f"[OCR Error] {result.get('ErrorMessage', 'Unknown')}"

    lines = []
    for i, r in enumerate(result.get("ParsedResults", []), 1):
        text = r.get("ParsedText", "").strip()
        if text:
            if i > 1:
                lines.append(f"\n--- Page {i} ---")
            lines.append(text)

    if not lines:
        return "[No text found in image]"

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Read text from screenshot via OCR.Space")
    ap.add_argument("image", help="Path to PNG/JPEG image")
    ap.add_argument("--lang", default="chs", help="OCR language: chs, eng, etc.")
    ap.add_argument("--raw", action="store_true", help="Output raw JSON")
    args = ap.parse_args()

    result = ocr_image(args.image, args.lang)
    if args.raw:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        output = format_result(result)
        print(output)
        # Show OCR confidence
        for r in result.get("ParsedResults", []):
            ocr_exit = r.get("OCRExitCode", 0)
            if ocr_exit != 1:
                print(f"\n[OCR Exit Code: {ocr_exit} (1=good)]")


if __name__ == "__main__":
    main()
