#!/usr/bin/env python3
"""P5.7 auto-select wrapper for local poster generation.

This script runs the P5.6 matrix, reads scores.json, and decides whether the
best poster is clear enough to send automatically. It intentionally does not
send Telegram messages itself; it writes a send_manifest.json that the agent can
use with the message tool without exposing chat credentials to local scripts.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def run_matrix(image: Path, style: str, output_dir: Path, include_p54: bool, auto_photo_position: bool, ai_copy: bool = False, auto_color: bool = False) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "tools/poster_version_matrix.py"),
        "--image",
        str(image),
        "--style",
        style,
        "--output-dir",
        str(output_dir),
    ]
    if include_p54:
        cmd.append("--include-p54")
    if auto_photo_position:
        cmd.append("--auto-photo-position")
    if ai_copy:
        cmd.append("--ai-copy")
    if auto_color:
        cmd.append("--auto-color")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=360)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"P5.6 matrix failed:\n{combined}")


def load_scores(run_dir: Path) -> list[dict[str, Any]]:
    scores_path = run_dir / "scores.json"
    if not scores_path.exists():
        raise FileNotFoundError(scores_path)
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    if not scores:
        raise ValueError(f"No scores found in {scores_path}")
    return scores


def decide(scores: list[dict[str, Any]], score_gap: float) -> tuple[str, dict[str, Any], float]:
    best = scores[0]
    second = scores[1] if len(scores) > 1 else None
    gap = float(best["score"]) - float(second["score"]) if second else 999.0
    if gap < score_gap:
        return "needs_review", best, round(gap, 3)
    return "auto_selected", best, round(gap, 3)


def write_manifest(
    run_dir: Path,
    source: Path,
    scores: list[dict[str, Any]],
    decision: str,
    best: dict[str, Any],
    gap: float,
    score_gap: float,
) -> Path:
    best_image = Path(str(best["image"]))
    comparison = run_dir / "comparison.jpg"
    report = run_dir / "report.md"
    selected_copy = run_dir / "selected_best.jpg"
    if best_image.exists():
        shutil.copy2(best_image, selected_copy)

    summary_lines = [
        "# P5.7 Auto Select",
        "",
        f"- Decision: `{decision}`",
        f"- Source: `{source}`",
        f"- Best: `{best['name']}` score `{best['score']}`",
        f"- Gap to second: `{gap}` (threshold `{score_gap}`)",
        f"- Recommendation: `{best['recommendation']}`",
        "",
        "| Rank | Version | Score | Grade | Warnings |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for rank, item in enumerate(scores, start=1):
        warnings = ", ".join(item.get("warnings", [])) or "none"
        summary_lines.append(f"| {rank} | `{item['name']}` | {item['score']} | {item['grade']} | {warnings} |")
    summary_lines.append("")

    summary_path = run_dir / "telegram_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    manifest = {
        "decision": decision,
        "source": str(source),
        "run_dir": str(run_dir),
        "score_gap": score_gap,
        "actual_gap": gap,
        "best": best,
        "selected_image": str(selected_copy if selected_copy.exists() else best_image),
        "comparison_image": str(comparison),
        "matrix_report": str(report),
        "telegram_summary": str(summary_path),
        "ranked": scores,
    }
    manifest_path = run_dir / "send_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P5.7 poster auto-selection.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--style", choices=["food", "teacher", "community"], default="food")
    parser.add_argument("--score-gap", type=float, default=2.0)
    parser.add_argument("--include-p54", action="store_true")
    parser.add_argument("--auto-photo-position", action="store_true", help="Use face/subject-aware crop positioning.")
    parser.add_argument("--ai-copy", action="store_true", help="Generate copy using local Qwen.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source.")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (args.output_dir or REPORTS / "auto_select" / f"poster_auto_select_{timestamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    run_matrix(args.image.resolve(), args.style, run_dir, args.include_p54, args.auto_photo_position, args.ai_copy, args.auto_color)
    scores = load_scores(run_dir)
    decision, best, gap = decide(scores, args.score_gap)
    manifest = write_manifest(run_dir, args.image.resolve(), scores, decision, best, gap, args.score_gap)

    print(f"decision={decision}")
    print(f"best={best['name']} score={best['score']} gap={gap}")
    print(f"run_dir={run_dir}")
    print(f"manifest={manifest}")


if __name__ == "__main__":
    main()
