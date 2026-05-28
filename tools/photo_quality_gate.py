#!/usr/bin/env python3
"""Deterministic quality gate for local photo processing.

This script scores source photos before enhancement/upscale/OCR/poster use. It
uses only OpenCV and NumPy so it can run inside the current workspace without
new model downloads or extra Python packages.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class PhotoQualityResult:
    image: str
    score: float
    grade: str
    recommendation: str
    width: int
    height: int
    megapixels: float
    aspect_ratio: float
    luma_mean: float
    luma_std: float
    saturation_mean: float
    saturation_p95: float
    sharpness: float
    highlight_pct: float
    shadow_pct: float
    noise_estimate: float
    color_cast_delta: float
    red_dominance_pct: float
    skin_pct: float
    skin_luma_mean: float | None
    skin_saturation_mean: float | None
    warnings: list[str]


def _read_bgr(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def _working_copy(bgr: np.ndarray, max_edge: int = 1400) -> np.ndarray:
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


def _noise_estimate(gray: np.ndarray) -> float:
    # Median residual is a cheap, deterministic noise proxy. It avoids the
    # high-frequency edge bias of raw Laplacian variance.
    smoothed = cv2.medianBlur(gray, 3)
    residual = cv2.absdiff(gray, smoothed)
    return float(np.percentile(residual, 90))


def _color_cast_delta(bgr: np.ndarray) -> float:
    means = bgr.reshape(-1, 3).mean(axis=0)
    return float(max(means) - min(means))


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
        return "ready for processing"
    if "too small" in joined:
        return "prefer upscale or request higher-resolution source"
    if "soft" in joined or "blur" in joined:
        return "run conservative sharpen or RealESRGAN upscale"
    if "dark" in joined or "flat" in joined or "color cast" in joined:
        return "run local photo enhance preset p53 or portrait"
    if "skin" in joined or "red" in joined or "saturation" in joined:
        return "use natural/skin-safe enhancement"
    if score >= 78:
        return "usable, compare by eye after enhancement"
    return "needs correction before poster or delivery"


def score_photo(path: Path) -> PhotoQualityResult:
    original = _read_bgr(path)
    bgr = _working_copy(original)
    height, width = original.shape[:2]
    megapixels = (width * height) / 1_000_000
    aspect_ratio = width / max(height, 1)

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
    noise = _noise_estimate(gray)
    color_cast = _color_cast_delta(bgr)
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

    if min(width, height) < 720 or megapixels < 0.75:
        score -= 14.0
        warnings.append("image too small for reliable delivery")
    elif min(width, height) < 1080 or megapixels < 1.5:
        score -= 6.0
        warnings.append("image resolution modest")

    if luma_mean < 82:
        score -= min(18.0, (82.0 - luma_mean) * 0.28)
        warnings.append("image is dark")
    elif luma_mean > 202:
        score -= min(16.0, (luma_mean - 202.0) * 0.27)
        warnings.append("image is bright")

    if luma_std < 34:
        score -= min(12.0, (34.0 - luma_std) * 0.38)
        warnings.append("low contrast / flat")
    elif luma_std > 92:
        score -= min(8.0, (luma_std - 92.0) * 0.14)
        warnings.append("harsh contrast")

    if sat_mean > 118:
        score -= min(14.0, (sat_mean - 118.0) * 0.22)
        warnings.append("overall saturation high")
    elif sat_mean < 30:
        score -= min(8.0, (30.0 - sat_mean) * 0.16)
        warnings.append("overall saturation low")

    if sat_p95 > 215:
        score -= min(10.0, (sat_p95 - 215.0) * 0.11)
        warnings.append("peak saturation high")

    if sharpness < 45:
        score -= min(20.0, (45.0 - sharpness) * 0.28)
        warnings.append("low sharpness / blur")
    elif sharpness > 1500:
        score -= 4.0
        warnings.append("possible oversharpening")

    if highlight_pct > 8.0:
        score -= min(14.0, (highlight_pct - 8.0) * 0.9)
        warnings.append("highlight clipping")
    if shadow_pct > 8.0:
        score -= min(14.0, (shadow_pct - 8.0) * 0.85)
        warnings.append("shadow crushing")

    if noise > 11.0:
        score -= min(12.0, (noise - 11.0) * 0.75)
        warnings.append("visible noise risk")
    if color_cast > 24.0:
        score -= min(10.0, (color_cast - 24.0) * 0.25)
        warnings.append("white balance / color cast risk")
    if red_dominance_pct > 12.0:
        score -= min(10.0, (red_dominance_pct - 12.0) * 0.65)
        warnings.append("red dominance risk")

    if skin_luma_mean is not None and skin_sat_mean is not None:
        if skin_luma_mean < 82:
            score -= min(8.0, (82.0 - skin_luma_mean) * 0.14)
            warnings.append("skin too dark")
        elif skin_luma_mean > 210:
            score -= min(8.0, (skin_luma_mean - 210.0) * 0.16)
            warnings.append("skin too bright")
        if skin_sat_mean > 112:
            score -= min(10.0, (skin_sat_mean - 112.0) * 0.16)
            warnings.append("skin saturation high")

    score = round(float(np.clip(score, 0.0, 100.0)), 2)
    return PhotoQualityResult(
        image=str(path),
        score=score,
        grade=_grade(score),
        recommendation=_recommendation(score, warnings),
        width=width,
        height=height,
        megapixels=round(megapixels, 3),
        aspect_ratio=round(aspect_ratio, 3),
        luma_mean=round(luma_mean, 2),
        luma_std=round(luma_std, 2),
        saturation_mean=round(sat_mean, 2),
        saturation_p95=round(sat_p95, 2),
        sharpness=round(sharpness, 2),
        highlight_pct=highlight_pct,
        shadow_pct=shadow_pct,
        noise_estimate=round(noise, 2),
        color_cast_delta=round(color_cast, 2),
        red_dominance_pct=red_dominance_pct,
        skin_pct=skin_pct,
        skin_luma_mean=round(skin_luma_mean, 2) if skin_luma_mean is not None else None,
        skin_saturation_mean=round(skin_sat_mean, 2) if skin_sat_mean is not None else None,
        warnings=warnings,
    )


def _markdown(result: PhotoQualityResult) -> str:
    warnings = ", ".join(result.warnings) if result.warnings else "none"
    return "\n".join(
        [
            "# Photo Quality Gate",
            "",
            f"- Image: `{result.image}`",
            f"- Score: `{result.score}` / 100",
            f"- Grade: `{result.grade}`",
            f"- Recommendation: `{result.recommendation}`",
            f"- Size: `{result.width}x{result.height}` ({result.megapixels} MP, aspect {result.aspect_ratio})",
            f"- Luma: mean `{result.luma_mean}`, std `{result.luma_std}`",
            f"- Saturation: mean `{result.saturation_mean}`, p95 `{result.saturation_p95}`",
            f"- Sharpness: `{result.sharpness}`",
            f"- Highlight/shadow: `{result.highlight_pct}%` / `{result.shadow_pct}%`",
            f"- Noise estimate: `{result.noise_estimate}`",
            f"- Color cast delta: `{result.color_cast_delta}`",
            f"- Red dominance: `{result.red_dominance_pct}%`",
            f"- Skin: `{result.skin_pct}%`, luma `{result.skin_luma_mean}`, saturation `{result.skin_saturation_mean}`",
            f"- Warnings: {warnings}",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a source photo for local processing readiness.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    args = parser.parse_args()

    result = score_photo(args.image)
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
