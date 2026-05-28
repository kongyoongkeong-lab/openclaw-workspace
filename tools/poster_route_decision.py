#!/usr/bin/env python3
"""P5.8 local photo routing for poster generation.

The router inspects the input photo and decides which existing poster workflow
should handle it. It uses deterministic OpenCV metrics only; no API, model, or
GPU work is required.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


@dataclass
class RouteDecision:
    image: str
    scene_type: str
    style: str
    primary_pipeline: str
    p54_recommended: bool
    include_p54: bool
    confidence: float
    reason: list[str]
    metrics: dict[str, float | int | str]
    command: list[str]


def _read_bgr(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def _working_copy(bgr: np.ndarray, max_edge: int = 1200) -> np.ndarray:
    height, width = bgr.shape[:2]
    largest = max(height, width)
    if largest <= max_edge:
        return bgr
    scale = max_edge / largest
    return cv2.resize(bgr, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)


def _pct(mask: np.ndarray) -> float:
    return round(float(mask.mean() * 100.0), 3)


def _skin_mask(bgr: np.ndarray) -> np.ndarray:
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    y_chan, cr_chan, cb_chan = cv2.split(ycrcb)
    return (
        (cr_chan >= 132)
        & (cr_chan <= 178)
        & (cb_chan >= 72)
        & (cb_chan <= 132)
        & (y_chan >= 42)
    )


def analyze_image(path: Path) -> dict[str, float | int | str]:
    original = _read_bgr(path)
    bgr = _working_copy(original)
    height, width = original.shape[:2]
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    skin_pct = _pct(_skin_mask(bgr))
    red_pct = _pct(((hue <= 8) | (hue >= 172)) & (sat > 90) & (val > 45))
    warm_food_pct = _pct((hue >= 5) & (hue <= 35) & (sat > 65) & (val > 55))
    green_pct = _pct((hue >= 35) & (hue <= 90) & (sat > 45) & (val > 50))
    neutral_pct = _pct((sat < 45) & (val > 80))
    bright_pct = _pct(val > 235)
    dark_pct = _pct(val < 32)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    aspect = width / max(height, 1)
    orientation = "portrait" if height > width else "landscape" if width > height else "square"

    return {
        "width": width,
        "height": height,
        "orientation": orientation,
        "aspect_ratio": round(aspect, 3),
        "luma_mean": round(float(gray.mean()), 2),
        "luma_std": round(float(gray.std()), 2),
        "saturation_mean": round(float(sat.mean()), 2),
        "saturation_p95": round(float(np.percentile(sat, 95)), 2),
        "skin_pct": skin_pct,
        "red_pct": red_pct,
        "warm_food_pct": warm_food_pct,
        "green_pct": green_pct,
        "neutral_pct": neutral_pct,
        "bright_pct": bright_pct,
        "dark_pct": dark_pct,
        "sharpness": round(sharpness, 2),
    }


def decide_route(path: Path, topic_hint: str = "", allow_p54: bool = False, ai_copy: bool = False, auto_color: bool = False) -> RouteDecision:
    metrics = analyze_image(path)
    hint = topic_hint.lower()
    reason: list[str] = []

    skin_pct = float(metrics["skin_pct"])
    warm_food_pct = float(metrics["warm_food_pct"])
    red_pct = float(metrics["red_pct"])
    sharpness = float(metrics["sharpness"])
    luma_mean = float(metrics["luma_mean"])
    luma_std = float(metrics["luma_std"])

    if any(token in hint for token in ("teacher", "老师", "教师", "感恩")):
        style = "teacher"
        scene_type = "teacher_or_appreciation"
        reason.append("topic hint points to teacher/appreciation content")
    elif any(
        token in hint
        for token in (
            "community",
            "activity",
            "event",
            "portrait",
            "lifestyle",
            "casual",
            "cafe",
            "person",
            "people",
            "活动",
            "社区",
            "合照",
            "关怀",
            "人物",
            "人像",
            "生活",
            "生活照",
            "咖啡",
            "咖啡店",
        )
    ):
        style = "community"
        scene_type = "community_or_event"
        reason.append("topic hint points to community/event/portrait content")
    elif any(token in hint for token in ("food", "美食", "汤", "小贩", "摊", "店")):
        style = "food"
        scene_type = "food_or_shop"
        reason.append("topic hint points to food/shop content")
    elif skin_pct >= 18 and warm_food_pct >= 8:
        style = "food"
        scene_type = "person_food_shop"
        reason.append("skin and warm-food color regions are both significant")
    elif skin_pct >= 18:
        style = "community"
        scene_type = "person_or_event"
        reason.append("skin region is significant; prefer natural people-safe layout")
    elif warm_food_pct >= 12 or red_pct >= 10:
        style = "food"
        scene_type = "food_or_product"
        reason.append("warm/red object regions suggest food or product emphasis")
    else:
        style = "community"
        scene_type = "general_lifestyle"
        reason.append("no dominant food/person signal; use general community style")

    p54_recommended = False
    if sharpness < 80 or min(int(metrics["width"]), int(metrics["height"])) < 900:
        p54_recommended = True
        if allow_p54:
            reason.append("low sharpness or small source dimensions; P5.4 enabled for clarity")
        else:
            reason.append("low sharpness or small source dimensions; P5.4 recommended but disabled by default")
    if luma_mean < 95 or luma_std < 35:
        reason.append("dim or flat source; P5.3 correction should be included")
    if skin_pct >= 18:
        primary_pipeline = "p57_auto_select_p53_v62_people_safe"
    elif scene_type == "food_or_product":
        primary_pipeline = "p57_auto_select_with_v3_impact"
    else:
        primary_pipeline = "p57_auto_select_general"

    confidence = 0.58
    if topic_hint:
        confidence += 0.18
    if skin_pct >= 18 or warm_food_pct >= 12:
        confidence += 0.14
    include_p54 = bool(p54_recommended and allow_p54)
    if include_p54:
        confidence -= 0.06
    confidence = round(float(np.clip(confidence, 0.35, 0.95)), 2)

    command = [
        str(ROOT / "tools/poster_auto_select.py"),
        "--image",
        str(path),
        "--style",
        style,
        "--auto-photo-position",
    ]
    if include_p54:
        command.append("--include-p54")
    if ai_copy:
        command.append("--ai-copy")
    if auto_color:
        command.append("--auto-color")

    return RouteDecision(
        image=str(path),
        scene_type=scene_type,
        style=style,
        primary_pipeline=primary_pipeline,
        p54_recommended=p54_recommended,
        include_p54=include_p54,
        confidence=confidence,
        reason=reason,
        metrics=metrics,
        command=command,
    )


def write_decision(decision: RouteDecision, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(asdict(decision), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_auto_select(decision: RouteDecision, output_dir: Path) -> Path:
    cmd = [sys.executable, *decision.command]
    cmd.extend(["--output-dir", str(output_dir)])
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=420)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"P5.7 auto-select failed:\n{combined}")
    manifest = output_dir / "send_manifest.json"
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P5.8 poster route decision.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--topic-hint", default="")
    parser.add_argument("--allow-p54", action="store_true", help="Allow route to pass --include-p54 to P5.7.")
    parser.add_argument("--ai-copy", action="store_true", help="Generate copy using local Qwen.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run-auto-select", action="store_true")
    parser.add_argument("--auto-output-dir", type=Path)
    args = parser.parse_args()

    image = args.image.resolve()
    decision = decide_route(image, args.topic_hint, args.allow_p54, args.ai_copy, args.auto_color)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = (args.output or REPORTS / "routes" / f"route_decision_{timestamp}.json").resolve()
    write_decision(decision, output)

    print(json.dumps(asdict(decision), ensure_ascii=False, indent=2))
    print(f"route_decision={output}")
    if args.run_auto_select:
        run_dir = (args.auto_output_dir or REPORTS / "auto_select" / f"poster_auto_select_{timestamp}").resolve()
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest = run_auto_select(decision, run_dir)
        print(f"send_manifest={manifest}")


if __name__ == "__main__":
    main()
