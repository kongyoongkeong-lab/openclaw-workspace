#!/usr/bin/env python3
"""P5.9 one-command poster entrypoint.

This wraps:
1. P5.8 route decision
2. P5.7 auto-select
3. Agent-facing send manifest

The script does not send Telegram messages. It prepares a compact
make_manifest.json so the agent can safely call the message tool.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def run_route(
    image: Path,
    topic_hint: str,
    run_dir: Path,
    allow_p54: bool,
    ai_copy: bool = False,
    auto_color: bool = False,
) -> tuple[Path, Path]:
    route_path = run_dir / "route_decision.json"
    auto_dir = run_dir / "auto_select"
    cmd = [
        sys.executable,
        str(ROOT / "tools/poster_route_decision.py"),
        "--image",
        str(image),
        "--output",
        str(route_path),
        "--run-auto-select",
        "--auto-output-dir",
        str(auto_dir),
    ]
    if topic_hint:
        cmd.extend(["--topic-hint", topic_hint])
    if allow_p54:
        cmd.append("--allow-p54")
    if ai_copy:
        cmd.append("--ai-copy")
    if auto_color:
        cmd.append("--auto-color")

    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=480)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"P5.9 route chain failed:\n{combined}")

    manifest_path = auto_dir / "send_manifest.json"
    if not route_path.exists():
        raise FileNotFoundError(route_path)
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    return route_path, manifest_path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_caption(route: dict[str, Any], send_manifest: dict[str, Any]) -> str:
    best = send_manifest["best"]
    decision = send_manifest["decision"]
    lines = [
        f"P5.9 海报完成：`{decision}`",
        f"路由：`{route['scene_type']}` / style `{route['style']}` / confidence `{route['confidence']}`",
        f"最佳候选：`{best['name']}`，score `{best['score']}`",
    ]
    if route.get("p54_recommended") and not route.get("include_p54"):
        lines.append("P5.4：已建议但未启用，避免默认占用 GPU。")
    if decision == "needs_review":
        lines.append("前两名分差过小，建议看对比图后定稿。")
    return "\n".join(lines)


def build_make_manifest(
    image: Path,
    topic_hint: str,
    run_dir: Path,
    route_path: Path,
    send_manifest_path: Path,
) -> dict[str, Any]:
    route = load_json(route_path)
    send_manifest = load_json(send_manifest_path)
    decision = send_manifest["decision"]

    attachments = [send_manifest["selected_image"]]
    if decision == "needs_review":
        attachments.append(send_manifest["comparison_image"])

    return {
        "source": str(image),
        "topic_hint": topic_hint,
        "run_dir": str(run_dir),
        "decision": decision,
        "route_decision": str(route_path),
        "send_manifest": str(send_manifest_path),
        "selected_image": send_manifest["selected_image"],
        "comparison_image": send_manifest["comparison_image"],
        "telegram_summary": send_manifest["telegram_summary"],
        "recommended_attachments": attachments,
        "caption": build_caption(route, send_manifest),
        "route": route,
        "selection": send_manifest,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the P5.9 one-command poster pipeline.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--hint", "--topic-hint", dest="topic_hint", default="")
    parser.add_argument("--allow-p54", action="store_true")
    parser.add_argument("--ai-copy", action="store_true", help="Generate copy using local Qwen 3.5.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source photo.")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    image = args.image.resolve()
    if not image.exists():
        raise SystemExit(f"Image not found: {image}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (args.output_dir or REPORTS / "make_poster" / f"make_poster_{timestamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    route_path, send_manifest_path = run_route(image, args.topic_hint, run_dir, args.allow_p54, args.ai_copy, args.auto_color)
    manifest = build_make_manifest(image, args.topic_hint, run_dir, route_path, send_manifest_path)
    manifest_path = run_dir / "make_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"decision={manifest['decision']}")
    print(f"style={manifest['route']['style']} scene={manifest['route']['scene_type']}")
    print(f"selected={manifest['selected_image']}")
    if manifest["decision"] == "needs_review":
        print(f"comparison={manifest['comparison_image']}")
    print(f"make_manifest={manifest_path}")


if __name__ == "__main__":
    main()
