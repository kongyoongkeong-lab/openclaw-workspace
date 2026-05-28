#!/usr/bin/env python3
"""Local photo enhancement for poster inputs.

This is the P5 pre-processing layer for the local poster pipeline. It keeps
the image realistic while improving Telegram-compressed photos before layout.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def _gray_world_white_balance(bgr: np.ndarray, strength: float) -> np.ndarray:
    img = bgr.astype(np.float32)
    means = img.reshape(-1, 3).mean(axis=0)
    gray = float(means.mean())
    scale = gray / np.maximum(means, 1.0)
    balanced = np.clip(img * scale, 0, 255)
    return np.clip(img * (1.0 - strength) + balanced * strength, 0, 255).astype(np.uint8)


def _auto_gamma(bgr: np.ndarray, target: float, strength: float) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mean = max(float(gray.mean()) / 255.0, 0.01)
    gamma = np.log(target) / np.log(mean)
    gamma = float(np.clip(gamma, 0.72, 1.35))
    table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    corrected = cv2.LUT(bgr, table)
    return cv2.addWeighted(bgr, 1.0 - strength, corrected, strength, 0)


def _clahe_luma(bgr: np.ndarray, clip_limit: float) -> np.ndarray:
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_chan, a_chan, b_chan = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_chan = clahe.apply(l_chan)
    return cv2.cvtColor(cv2.merge((l_chan, a_chan, b_chan)), cv2.COLOR_LAB2BGR)


def _vibrance(bgr: np.ndarray, sat_gain: float, value_gain: float) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    sat = hsv[:, :, 1]
    low_sat_boost = 1.0 + sat_gain * (1.0 - sat / 255.0)
    hsv[:, :, 1] = np.clip(sat * low_sat_boost, 0, 255)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * value_gain, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _unsharp(bgr: np.ndarray, amount: float, radius: float) -> np.ndarray:
    blurred = cv2.GaussianBlur(bgr, (0, 0), radius)
    return cv2.addWeighted(bgr, 1.0 + amount, blurred, -amount, 0)


def _p53_skin_safe_guard(original: np.ndarray, enhanced: np.ndarray, strength: float) -> np.ndarray:
    """Keep real-person shop photos natural after enhancement.

    P5.3 is tuned for Telegram food-stall portraits: protect skin chroma,
    prevent red shirts/plastic bags from becoming neon, and keep white tile
    walls neutral without flattening the scene.
    """
    strength = float(np.clip(strength, 0.0, 1.0))
    out = enhanced.copy()

    ycrcb = cv2.cvtColor(original, cv2.COLOR_BGR2YCrCb)
    y_chan, cr_chan, cb_chan = cv2.split(ycrcb)
    skin_mask = (
        (cr_chan >= 132)
        & (cr_chan <= 178)
        & (cb_chan >= 72)
        & (cb_chan <= 132)
        & (y_chan >= 42)
    )

    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    # Red objects are common in hawker photos. Heavy enhancement makes them
    # dominate faces, so reduce only high-saturation non-skin reds.
    red_mask = (((hue <= 8) | (hue >= 172)) & (sat > 92) & (val > 45) & ~skin_mask)
    hsv[:, :, 1][red_mask] *= 1.0 - 0.16 * strength
    hsv[:, :, 2][red_mask] *= 1.0 - 0.035 * strength

    # White tile/wall regions should read neutral, not green/yellow/gray.
    wall_mask = (sat < 48) & (val > 104) & ~skin_mask
    hsv[:, :, 1][wall_mask] *= 1.0 - 0.22 * strength
    hsv[:, :, 2][wall_mask] = np.clip(hsv[:, :, 2][wall_mask] * (1.0 + 0.025 * strength), 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    # Blend skin back toward the original photo so wrinkles and local skin tone
    # stay believable while still benefiting from exposure correction.
    skin_soft = cv2.GaussianBlur(skin_mask.astype(np.float32), (0, 0), 3.0)
    skin_soft = np.clip(skin_soft * (0.34 * strength), 0, 0.34)[:, :, None]
    out = out.astype(np.float32) * (1.0 - skin_soft) + original.astype(np.float32) * skin_soft
    return np.clip(out, 0, 255).astype(np.uint8)


def enhance_image(
    input_path: Path,
    output_path: Path,
    preset: str = "poster",
    strength: float = 1.0,
) -> dict[str, float | str]:
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    bgr = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"Unable to read image: {input_path}")

    strength = float(np.clip(strength, 0.0, 1.5))
    before_mean = float(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).mean())

    # Conservative defaults: clean enough for posters without making real
    # people look synthetic.
    settings = {
        "poster": (0.42, 0.33, 2.0, 0.24, 1.03, 0.42, 1.0),
        "food": (0.38, 0.35, 2.15, 0.30, 1.04, 0.46, 1.0),
        "portrait": (0.30, 0.28, 1.8, 0.18, 1.02, 0.28, 0.9),
        "soft": (0.22, 0.20, 1.55, 0.13, 1.01, 0.22, 0.8),
        "p53": (0.26, 0.24, 1.65, 0.14, 1.015, 0.24, 0.85),
    }
    wb_s, gamma_s, clahe_clip, sat_gain, val_gain, sharp_amt, sharp_radius = settings[preset]

    out = _gray_world_white_balance(bgr, wb_s * strength)
    out = _auto_gamma(out, target=0.54, strength=gamma_s * strength)
    out = _clahe_luma(out, clip_limit=clahe_clip)
    out = cv2.addWeighted(bgr, max(0.0, 0.28 - 0.1 * strength), out, min(1.0, 0.72 + 0.1 * strength), 0)

    if strength >= 0.75:
        out = cv2.fastNlMeansDenoisingColored(out, None, 3, 3, 7, 21)

    out = _vibrance(out, sat_gain=sat_gain * strength, value_gain=val_gain)
    out = _unsharp(out, amount=sharp_amt * strength, radius=sharp_radius)
    out = np.clip(out, 0, 255).astype(np.uint8)
    if preset == "p53":
        out = _p53_skin_safe_guard(bgr, out, min(strength, 1.0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(output_path), out, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    if not ok:
        raise ValueError(f"Unable to write image: {output_path}")

    after_mean = float(cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).mean())
    return {
        "input": str(input_path),
        "output": str(output_path),
        "preset": preset,
        "strength": round(strength, 3),
        "mean_luma_before": round(before_mean, 2),
        "mean_luma_after": round(after_mean, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enhance a local photo for poster rendering.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preset", choices=["poster", "food", "portrait", "soft", "p53"], default="poster")
    parser.add_argument("--strength", type=float, default=1.0)
    args = parser.parse_args()

    result = enhance_image(args.image, args.output, args.preset, args.strength)
    print(result["output"])
    print(
        f"preset={result['preset']} strength={result['strength']} "
        f"luma={result['mean_luma_before']}->{result['mean_luma_after']}"
    )


if __name__ == "__main__":
    main()
