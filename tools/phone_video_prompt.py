#!/usr/bin/env python3
"""Prompt and phone-MP4 helper for short vertical video workflows."""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_NEGATIVE = (
    "no text, no watermark, no logo, no subtitles, no distorted hands, "
    "no extra fingers, no extra limbs, no flicker, no warped face"
)


def ffmpeg_path() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "ffmpeg not found on PATH and imageio-ffmpeg is unavailable"
        ) from exc

    return imageio_ffmpeg.get_ffmpeg_exe()


def build_prompts(args: argparse.Namespace) -> dict[str, str | dict[str, str | int]]:
    subject = args.subject.strip()
    action = args.action.strip()
    scene = args.scene.strip()
    style = args.style.strip()
    lighting = args.lighting.strip()
    camera = args.camera.strip()
    negative = args.negative.strip()

    image_prompt = (
        f"Create a vertical 9:16 high-resolution image for phone video animation. "
        f"Subject: {subject}. Scene: {scene}. Style: {style}. Lighting: {lighting}. "
        "Composition: centered subject, clean readable silhouette, natural depth, "
        "enough headroom for vertical phone framing. "
        f"Avoid: {negative}."
    )

    video_prompt = (
        f"Vertical 9:16 phone video, {args.duration} seconds, {args.fps} fps. "
        f"{subject} {action} in {scene}. "
        f"Camera: {camera}. Style: {style}. Lighting: {lighting}. "
        "Motion should be smooth, physically plausible, stable, and social-media-ready. "
        f"Avoid: {negative}."
    )

    return {
        "target": {
            "container": "mp4",
            "video_codec": "h264",
            "audio_codec": "aac",
            "pixel_format": "yuv420p",
            "aspect_ratio": "9:16",
            "resolution": args.resolution,
            "fps": args.fps,
            "duration_seconds": args.duration,
        },
        "google_banana_image_prompt": image_prompt,
        "google_veo_video_prompt": video_prompt,
    }


def normalize_phone_mp4(args: argparse.Namespace) -> int:
    src = Path(args.input).expanduser().resolve()
    dst = Path(args.output).expanduser().resolve()
    if not src.exists():
        print(f"input_not_found: {src}", file=sys.stderr)
        return 2

    width, height = args.resolution.lower().split("x", 1)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"setsar=1,fps={args.fps},format=yuv420p"
    )

    command = [
        ffmpeg_path(),
        "-y",
        "-i",
        str(src),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        "-shortest",
        str(dst),
    ]

    if args.print_command:
        print(" ".join(shlex.quote(part) for part in command))
        if args.dry_run:
            return 0

    result = subprocess.run(command, check=False)
    return result.returncode


def prompt_command(args: argparse.Namespace) -> int:
    payload = build_prompts(args)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("[Google Banana image prompt]")
        print(payload["google_banana_image_prompt"])
        print()
        print("[Google/Veo video prompt]")
        print(payload["google_veo_video_prompt"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Google Banana/Veo prompts and normalize phone MP4 output."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prompt = sub.add_parser("prompt", help="Generate image/video prompts")
    prompt.add_argument("--subject", required=True)
    prompt.add_argument("--action", default="moves naturally with subtle cinematic motion")
    prompt.add_argument("--scene", default="a clean realistic environment")
    prompt.add_argument("--style", default="cinematic realistic")
    prompt.add_argument("--lighting", default="soft directional natural light")
    prompt.add_argument("--camera", default="slow handheld push-in with stable framing")
    prompt.add_argument("--negative", default=DEFAULT_NEGATIVE)
    prompt.add_argument("--duration", type=int, default=6)
    prompt.add_argument("--fps", type=int, default=30)
    prompt.add_argument("--resolution", default="1080x1920")
    prompt.add_argument("--json", action="store_true")
    prompt.set_defaults(func=prompt_command)

    normalize = sub.add_parser("normalize", help="Convert video to phone-safe MP4")
    normalize.add_argument("--input", required=True)
    normalize.add_argument("--output", required=True)
    normalize.add_argument("--resolution", default="1080x1920")
    normalize.add_argument("--fps", type=int, default=30)
    normalize.add_argument("--crf", type=int, default=20)
    normalize.add_argument("--preset", default="medium")
    normalize.add_argument("--print-command", action="store_true")
    normalize.add_argument("--dry-run", action="store_true")
    normalize.set_defaults(func=normalize_phone_mp4)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
