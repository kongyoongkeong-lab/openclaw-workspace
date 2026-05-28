#!/usr/bin/env python3
"""Analyze photo composition for local poster rendering.

The goal is practical, deterministic layout guidance:
- detect likely faces with OpenCV Haar cascades;
- estimate a subject center even when no face is found;
- recommend a CSS background-position that keeps people visible;
- flag text-panel overlap risks for common poster layouts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class LayoutAnalysis:
    image: str
    width: int
    height: int
    face_count: int
    primary_face: list[int] | None
    subject_center_pct: list[float]
    subject_box_pct: list[float] | None
    recommended_position: str
    text_zone_risk: str
    warnings: list[str]


def _read_bgr(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return image


def _cascade() -> cv2.CascadeClassifier:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    classifier = cv2.CascadeClassifier(str(cascade_path))
    if classifier.empty():
        raise RuntimeError(f"Unable to load OpenCV cascade: {cascade_path}")
    return classifier


def _faces(bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    found = _cascade().detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(38, 38))
    faces = [(int(x), int(y), int(w), int(h)) for x, y, w, h in found]
    faces.sort(key=lambda box: box[2] * box[3], reverse=True)
    return faces


def _skin_mask(bgr: np.ndarray) -> np.ndarray:
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    y_chan, cr_chan, cb_chan = cv2.split(ycrcb)
    return (
        (cr_chan >= 132)
        & (cr_chan <= 178)
        & (cb_chan >= 72)
        & (cb_chan <= 132)
        & (y_chan >= 45)
    )


def _subject_from_skin(bgr: np.ndarray) -> tuple[list[float], list[float] | None]:
    height, width = bgr.shape[:2]
    mask = _skin_mask(bgr).astype("uint8") * 255
    kernel = np.ones((9, 9), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > width * height * 0.004]
    if not contours:
        return [50.0, 44.0], None

    all_points = np.vstack(contours)
    x, y, w, h = cv2.boundingRect(all_points)
    center = [round((x + w / 2) / width * 100, 2), round((y + h / 2) / height * 100, 2)]
    box = [
        round(x / width * 100, 2),
        round(y / height * 100, 2),
        round((x + w) / width * 100, 2),
        round((y + h) / height * 100, 2),
    ]
    return center, box


def _recommend_position(center_pct: list[float], layout: str) -> str:
    x_pct, y_pct = center_pct
    x = min(62.0, max(38.0, x_pct))

    # CRITICAL: These layouts use background-position with background-size: cover.
    # For portrait photos in a portrait poster, cover scales the image to fill width,
    # cropping excess height from top/bottom. The background-position Y% means
    # "align point Y% of the image with point Y% of the container".
    #
    # If the face is at y_pct% of the original image height, using a Y value close
    # to the actual face position (or lower) keeps the head fully visible.
    # Clamping to conventional 34-58% ranges causes the head to be cropped because
    # the image is ~1.5x taller than the poster after cover scaling.
    #
    # Formula: use 60% of the face's Y position, capped at 25 max, 0 min.
    # This ensures the entire head stays visible while avoiding over-scrolling.

    if layout == "portrait-blessing":
        # Lower text panels need the face/upper body kept above the fold.
        y = min(44.0, max(30.0, y_pct))
    else:
        # All cover-based layouts: keep face area visible by using a
        # low Y value derived from the actual face position.
        y = max(0.0, min(y_pct * 0.65, 25.0))
    return f"{x:.0f}% {y:.0f}%"


def analyze_image(path: Path, layout: str = "portrait-blessing") -> LayoutAnalysis:
    bgr = _read_bgr(path)
    height, width = bgr.shape[:2]
    faces = _faces(bgr)
    warnings: list[str] = []

    if faces:
        x, y, w, h = faces[0]
        center = [round((x + w / 2) / width * 100, 2), round((y + h / 2) / height * 100, 2)]
        box = [
            round(x / width * 100, 2),
            round(y / height * 100, 2),
            round((x + w) / width * 100, 2),
            round((y + h) / height * 100, 2),
        ]
        primary_face = [x, y, w, h]
    else:
        center, box = _subject_from_skin(bgr)
        primary_face = None
        warnings.append("no face detected; used skin/saliency fallback")

    text_zone_risk = "low"
    if layout == "portrait-blessing" and center[1] > 62:
        text_zone_risk = "high"
        warnings.append("subject is low; bottom text panel may overlap subject")
    elif layout == "portrait-blessing" and center[1] > 54:
        text_zone_risk = "medium"
        warnings.append("subject is slightly low for bottom text panel")

    return LayoutAnalysis(
        image=str(path),
        width=width,
        height=height,
        face_count=len(faces),
        primary_face=primary_face,
        subject_center_pct=center,
        subject_box_pct=box,
        recommended_position=_recommend_position(center, layout),
        text_zone_risk=text_zone_risk,
        warnings=warnings,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze poster photo composition and safe background position.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--layout", default="portrait-blessing")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = analyze_image(args.image, args.layout)
    payload = asdict(result)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
