#!/usr/bin/env python3
"""P5.12 Auto color palette extraction from source photos.

Extracts dominant colors using KMeans clustering, then generates a coherent
poster-friendly palette: accent, accent2 (gradient), background tint, and
text-safe colors.

All local; no API call.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


@dataclass
class ColorPalette:
    image: str
    accent_hex: str
    accent2_hex: str
    bg_hex: str
    bg_dark_hex: str
    text_light_hex: str
    text_dark_hex: str
    accent_rgb: tuple[int, int, int]
    accent2_rgb: tuple[int, int, int]
    dominant_colors_hex: list[str]
    palette_type: str


def _read_bgr(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Unable to read: {path}")
    return image


def _bgr_to_hex(bgr: tuple[int, int, int]) -> str:
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    """Convert HSV (0-179, 0-255, 0-255) to hex."""
    h_deg = h / 179 * 180
    s_norm = s / 255.0
    v_norm = v / 255.0
    hi = int(h_deg / 60) % 6
    f_val = h_deg / 60 - hi
    p = int(v_norm * (1 - s_norm) * 255)
    q = int(v_norm * (1 - f_val * s_norm) * 255)
    t = int(v_norm * (1 - (1 - f_val) * s_norm) * 255)
    v255 = int(v_norm * 255)
    if hi == 0:
        bgr = (v255, t, p)
    elif hi == 1:
        bgr = (q, v255, p)
    elif hi == 2:
        bgr = (p, v255, t)
    elif hi == 3:
        bgr = (p, q, v255)
    elif hi == 4:
        bgr = (t, p, v255)
    else:
        bgr = (v255, p, q)
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


def _rgb_to_hsv(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Convert 0-255 RGB to OpenCV HSV (0-179, 0-255, 0-255)."""
    pixel = np.uint8([[[b, g, r]]])
    hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
    return int(hsv[0][0][0]), int(hsv[0][0][1]), int(hsv[0][0][2])


def _kmeans_palette(bgr: np.ndarray, k: int = 5) -> list[tuple[int, int, int]]:
    """Extract k dominant BGR colors using KMeans."""
    pixels = bgr.reshape(-1, 3).astype(np.float32)
    _, labels, centers = cv2.kmeans(
        pixels, k, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        10, cv2.KMEANS_RANDOM_CENTERS,
    )
    counts = np.bincount(labels.flatten())
    ordered = sorted(centers.astype(int).tolist(), key=lambda c: -counts[np.argmin(np.linalg.norm(centers - c, axis=1))])
    return [tuple(c) for c in ordered]


def _warmth_score(bgr: tuple[int, int, int]) -> float:
    """Higher means warmer/orange. Based on red/blue ratio."""
    b, g, r = bgr
    if b == 0 and r == 0:
        return 0.5
    return r / max(b, 1)


def _luminance(bgr: tuple[int, int, int]) -> float:
    """Perceived luminance 0-255."""
    b, g, r = bgr
    return 0.299 * r + 0.587 * g + 0.114 * b


def _is_saturated(bgr: tuple[int, int, int], threshold: int = 60) -> bool:
    _, _, s = _rgb_to_hsv(*bgr)
    return s > threshold


def _harmonize_accent(bgr: tuple[int, int, int], target_warm: bool = True) -> tuple[int, int, int]:
    """Shift color toward a pleasant warm or cool accent."""
    h, s, v = _rgb_to_hsv(*bgr)
    if target_warm:
        # Shift toward warm amber/copper band (10-30 deg)
        if h < 5 or h > 35:
            h = 22
        s = max(s, 180)
        v = max(v, 170)
    else:
        # Shift toward cool blue band
        h = 210
        s = max(s, 100)
        v = max(v, 160)
    return _hsv_to_rgb(h, min(s, 240), min(v, 240))


def _hsv_to_rgb(h: int, s: int, v: int) -> tuple[int, int, int]:
    """Convert OpenCV HSV to BGR tuple."""
    pixel = np.uint8([[[h, s, v]]])
    bgr = cv2.cvtColor(pixel, cv2.COLOR_HSV2BGR)
    return int(bgr[0][0][0]), int(bgr[0][0][1]), int(bgr[0][0][2])


def extract_palette(path: Path, style: str = "food") -> dict[str, Any]:
    """Extract color palette from image. Returns dict with hex colors."""
    bgr = _read_bgr(path)
    resized = cv2.resize(bgr, (200, 200), interpolation=cv2.INTER_AREA)

    dominant = _kmeans_palette(resized, k=5)
    dominant_hex = [_bgr_to_hex(c) for c in dominant]

    # Score each dominant color and pick the best accent based on style
    candidates = []
    for color in dominant:
        lum = _luminance(color)
        warm = _warmth_score(color)
        sat = _is_saturated(color)
        h, s_val, v_val = _rgb_to_hsv(*color)

        score = 0.0
        if style in ("food", "teacher", "blessing", "community"):
            # Prefer warm, moderately bright, not too dark, not too light
            if 30 < lum < 200:
                score += 0.4
            if warm > 1.2:
                score += 0.3
            if sat:
                score += 0.3
            # Brown/warm-grey range gets bonus
            if 5 <= h <= 30 and s_val > 60:
                score += 0.2
        elif style == "youth":
            # Prefer vibrant, cooler, bright
            if lum > 80:
                score += 0.3
            if sat:
                score += 0.4
            if h <= 30 or h >= 140:
                score += 0.3
        else:
            score = 1.0 - abs(128 - lum) / 256 + (0.3 if sat else 0)

        candidates.append((score, color, lum))

    candidates.sort(key=lambda x: -x[0])

    # Pick accent from top candidate; if it's grey, use second or harmonize
    accent_color = candidates[0][1]
    h, s_val, v_val = _rgb_to_hsv(*accent_color)
    if s_val < 50 and len(candidates) > 1:
        accent_color = candidates[1][1]

    palette_type = style

    if style in ("food", "teacher", "blessing", "community"):
        accent2_bgr = _harmonize_accent(accent_color, target_warm=True)
        bg_tint = tuple(max(0, min(255, c + 70)) for c in accent_color)
        bg_dark = tuple(max(0, c - 40) for c in accent_color)
        text_light = (255, 248, 230)
        text_dark = (62, 34, 16)
    elif style == "youth":
        accent2_bgr = _harmonize_accent(accent_color, target_warm=False)
        bg_tint = tuple(max(0, min(255, c + 90)) for c in accent_color)
        bg_dark = tuple(max(0, c - 50) for c in accent_color)
        text_light = (255, 252, 240)
        text_dark = (28, 28, 42)
    else:
        accent2_bgr = accent_color
        bg_tint = tuple(max(0, min(255, c + 80)) for c in accent_color)
        bg_dark = accent_color
        text_light = (255, 255, 255)
        text_dark = (30, 30, 30)

    return {
        "image": str(path),
        "accent_hex": _bgr_to_hex(accent_color),
        "accent2_hex": _bgr_to_hex(accent2_bgr),
        "bg_hex": _bgr_to_hex(bg_tint),
        "bg_dark_hex": _bgr_to_hex(bg_dark),
        "text_light_hex": _bgr_to_hex(text_light),
        "text_dark_hex": _bgr_to_hex(text_dark),
        "accent_rgb": [int(accent_color[2]), int(accent_color[1]), int(accent_color[0])],
        "accent2_rgb": [int(accent2_bgr[2]), int(accent2_bgr[1]), int(accent2_bgr[0])],
        "dominant_colors_hex": dominant_hex,
        "palette_type": palette_type,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="P5.12 Auto color palette extraction.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--style", choices=["food", "teacher", "community", "youth", "blessing"], default="food")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    palette = extract_palette(args.image.resolve(), args.style)
    print(json.dumps(palette, ensure_ascii=False, indent=2))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(palette, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
