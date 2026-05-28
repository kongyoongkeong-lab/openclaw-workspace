#!/usr/bin/env python3
"""Score local poster outputs with deterministic image metrics.

P5.5 is a lightweight gate for comparing P5.3, P5.4, V6.2, and V3 outputs.
It does not judge taste; it flags common local-poster failure modes:
overexposure, underexposure, oversaturated reds, soft output, and unnatural
skin color drift.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from poster_layout_guard import analyze_image


@dataclass
class QualityResult:
    image: str
    score: float
    grade: str
    recommendation: str
    width: int
    height: int
    luma_mean: float
    luma_std: float
    saturation_mean: float
    saturation_p95: float
    sharpness: float
    highlight_pct: float
    shadow_pct: float
    red_dominance_pct: float
    skin_pct: float
    skin_luma_mean: float | None
    skin_saturation_mean: float | None
    layout_face_count: int | None
    layout_subject_center_pct: list[float] | None
    layout_text_zone_risk: str | None
    warnings: list[str]


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


def _grade(score: float) -> str:
    if score >= 88:
        return "A"
    if score >= 78:
        return "B"
    if score >= 68:
        return "C"
    return "D"


def _recommendation(score: float, warnings: list[str]) -> str:
    joined = " ".join(warnings)
    if score >= 88 and not warnings:
        return "publish"
    if score >= 86:
        return "publish candidate, compare by eye"
    if "soft" in joined or "low sharpness" in joined:
        return "try P5.4 upscale"
    if "skin" in joined or "red" in joined or "saturation" in joined:
        return "try V6.2 soft natural mode"
    if "dark" in joined or "flat" in joined:
        return "try P5.3 p53 correction"
    if score >= 78:
        return "usable, compare by eye"
    return "regenerate or adjust enhancement"


def score_image(path: Path, source_image: Path | None = None, layout: str = "portrait-blessing") -> QualityResult:
    original = _read_bgr(path)
    bgr = _working_copy(original)
    height, width = original.shape[:2]

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    luma_mean = float(gray.mean())
    luma_std = float(gray.std())
    sat_mean = float(sat.mean())
    sat_p95 = float(np.percentile(sat, 95))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    highlight_pct = _pct(val > 245)
    shadow_pct = _pct(val < 24)
    red_mask = ((hue <= 8) | (hue >= 172)) & (sat > 100) & (val > 45)
    red_dominance_pct = _pct(red_mask)

    skin = _skin_mask(bgr)
    skin_pct = _pct(skin)
    skin_luma_mean: float | None = None
    skin_sat_mean: float | None = None
    if skin_pct >= 0.35:
        skin_luma_mean = float(gray[skin].mean())
        skin_sat_mean = float(sat[skin].mean())

    score = 100.0
    warnings: list[str] = []

    if luma_mean < 95:
        score -= min(16.0, (95.0 - luma_mean) * 0.23)
        warnings.append("image is dark")
    elif luma_mean > 192:
        score -= min(14.0, (luma_mean - 192.0) * 0.24)
        warnings.append("image is bright")

    if luma_std < 38:
        score -= min(12.0, (38.0 - luma_std) * 0.35)
        warnings.append("low contrast / flat")
    elif luma_std > 86:
        score -= min(8.0, (luma_std - 86.0) * 0.15)
        warnings.append("harsh contrast")

    if sat_mean > 112:
        score -= min(14.0, (sat_mean - 112.0) * 0.22)
        warnings.append("overall saturation high")
    elif sat_mean < 38:
        score -= min(8.0, (38.0 - sat_mean) * 0.14)
        warnings.append("overall saturation low")

    if sat_p95 > 205:
        score -= min(10.0, (sat_p95 - 205.0) * 0.10)
        warnings.append("peak saturation high")

    if sharpness < 55:
        score -= min(18.0, (55.0 - sharpness) * 0.22)
        warnings.append("low sharpness / soft")
    elif sharpness > 1250:
        score -= 4.0
        warnings.append("possible oversharpening")

    # Posters often contain white text and cream panels. Only penalize high
    # clipping after it becomes large enough to suggest image-level washout.
    if highlight_pct > 20.0:
        score -= min(13.0, (highlight_pct - 20.0) * 0.65)
        warnings.append("highlight clipping")
    if shadow_pct > 10.0:
        score -= min(12.0, (shadow_pct - 10.0) * 0.65)
        warnings.append("shadow crushing")
    if red_dominance_pct > 13.0:
        score -= min(12.0, (red_dominance_pct - 13.0) * 0.7)
        warnings.append("red dominance risk")

    if skin_luma_mean is not None and skin_sat_mean is not None:
        if skin_luma_mean < 86:
            score -= min(8.0, (86.0 - skin_luma_mean) * 0.14)
            warnings.append("skin too dark")
        elif skin_luma_mean > 205:
            score -= min(8.0, (skin_luma_mean - 205.0) * 0.16)
            warnings.append("skin too bright")
        if skin_sat_mean > 112:
            score -= min(10.0, (skin_sat_mean - 112.0) * 0.16)
            warnings.append("skin saturation high")

    layout_face_count: int | None = None
    layout_subject_center_pct: list[float] | None = None
    layout_text_zone_risk: str | None = None
    if source_image:
        try:
            layout_result = analyze_image(source_image, layout)
            layout_face_count = layout_result.face_count
            layout_subject_center_pct = layout_result.subject_center_pct
            layout_text_zone_risk = layout_result.text_zone_risk
            if layout_result.text_zone_risk == "high":
                score -= 10.0
                warnings.append("high text overlap risk")
            elif layout_result.text_zone_risk == "medium":
                score -= 4.0
                warnings.append("medium text overlap risk")
            if layout_result.face_count == 0:
                score -= 2.0
                warnings.append("no face detected in source")
        except Exception as exc:  # pragma: no cover - guard must not block image scoring.
            warnings.append(f"layout guard unavailable: {exc}")

    score = round(float(np.clip(score, 0.0, 100.0)), 2)
    return QualityResult(
        image=str(path),
        score=score,
        grade=_grade(score),
        recommendation=_recommendation(score, warnings),
        width=width,
        height=height,
        luma_mean=round(luma_mean, 2),
        luma_std=round(luma_std, 2),
        saturation_mean=round(sat_mean, 2),
        saturation_p95=round(sat_p95, 2),
        sharpness=round(sharpness, 2),
        highlight_pct=highlight_pct,
        shadow_pct=shadow_pct,
        red_dominance_pct=red_dominance_pct,
        skin_pct=skin_pct,
        skin_luma_mean=round(skin_luma_mean, 2) if skin_luma_mean is not None else None,
        skin_saturation_mean=round(skin_sat_mean, 2) if skin_sat_mean is not None else None,
        layout_face_count=layout_face_count,
        layout_subject_center_pct=layout_subject_center_pct,
        layout_text_zone_risk=layout_text_zone_risk,
        warnings=warnings,
    )


def _markdown(result: QualityResult) -> str:
    warnings = ", ".join(result.warnings) if result.warnings else "none"
    return "\n".join(
        [
            f"# Poster Quality Gate",
            "",
            f"- Image: `{result.image}`",
            f"- Score: `{result.score}` / 100",
            f"- Grade: `{result.grade}`",
            f"- Recommendation: `{result.recommendation}`",
            f"- Size: `{result.width}x{result.height}`",
            f"- Luma: mean `{result.luma_mean}`, std `{result.luma_std}`",
            f"- Saturation: mean `{result.saturation_mean}`, p95 `{result.saturation_p95}`",
            f"- Sharpness: `{result.sharpness}`",
            f"- Highlight/shadow: `{result.highlight_pct}%` / `{result.shadow_pct}%`",
            f"- Red dominance: `{result.red_dominance_pct}%`",
            f"- Skin: `{result.skin_pct}%`, luma `{result.skin_luma_mean}`, saturation `{result.skin_saturation_mean}`",
            f"- Layout guard: faces `{result.layout_face_count}`, subject `{result.layout_subject_center_pct}`, text risk `{result.layout_text_zone_risk}`",
            f"- Warnings: {warnings}",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a poster image for P5.5 quality routing.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--source-image", type=Path, help="Original source photo for face/text-safe layout checks.")
    parser.add_argument("--layout", default="portrait-blessing", help="Poster layout name for source-photo layout checks.")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    args = parser.parse_args()

    result = score_image(args.image, args.source_image, args.layout)
    payload = asdict(result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
