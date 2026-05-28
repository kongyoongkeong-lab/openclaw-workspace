#!/usr/bin/env python3
"""P5.13 Multi-language poster generation.

Generates CN/EN/BM versions of the same poster from one image.
Each language gets its own copy from the AI copy generator, but shares
the same photo enhancement, palette, and layout settings.
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


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


@dataclass
class I18nPosterResult:
    image: str
    style: str
    layout: str
    languages: list[str]
    outputs: dict[str, str]
    enhance_preset: str
    enhance_strength: float
    ai_copy: bool
    auto_color: bool
    run_dir: str
    warnings: list[str]


def generate_one(
    image: Path,
    output: Path,
    style: str,
    layout: str,
    language: str,
    enhance_preset: str,
    enhance_strength: float,
    ai_copy: bool,
    auto_color: bool,
    auto_photo_position: bool,
) -> None:
    """Generate one poster in a specific language."""
    cmd = [
        sys.executable,
        str(ROOT / "tools/local_poster_premium.py"),
        "--image", str(image),
        "--style", style,
        "--layout", layout,
        "--output", str(output),
        "--enhance",
        "--enhance-preset", enhance_preset,
        "--enhance-strength", str(enhance_strength),
    ]
    if ai_copy:
        cmd.extend(["--ai-copy", "--ai-copy-language", language])
    if auto_color:
        cmd.append("--auto-color")
    if auto_photo_position:
        cmd.append("--auto-photo-position")

    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=180)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"i18n poster failed for {language}:\n{combined}")
    print(f"[{language}] generated: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="P5.13 Multi-language poster generation.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--style", choices=["food", "teacher", "community", "youth", "blessing"], default="food")
    parser.add_argument("--layout", choices=["photo-large", "balanced", "story-cover", "editorial-cover", "natural-cover", "portrait-blessing"], default="natural-cover")
    parser.add_argument("--languages", nargs="+", choices=["cn", "en", "bm"], default=["cn", "en", "bm"])
    parser.add_argument("--enhance-preset", choices=["poster", "food", "portrait", "soft", "p53"], default="p53")
    parser.add_argument("--enhance-strength", type=float, default=0.48)
    parser.add_argument("--ai-copy", action="store_true", help="Use Qwen 3.5 to generate copy per language.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source photo.")
    parser.add_argument("--auto-photo-position", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (args.output_dir or REPORTS / "i18n" / f"i18n_poster_{timestamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    outputs: dict[str, str] = {}
    warnings: list[str] = []

    for lang in args.languages:
        out_path = run_dir / f"poster_{lang}.jpg"
        try:
            generate_one(
                image=args.image.resolve(),
                output=out_path,
                style=args.style,
                layout=args.layout,
                language=lang,
                enhance_preset=args.enhance_preset,
                enhance_strength=args.enhance_strength,
                ai_copy=args.ai_copy,
                auto_color=args.auto_color,
                auto_photo_position=args.auto_photo_position,
            )
            outputs[lang] = str(out_path)
        except RuntimeError as exc:
            warnings.append(f"{lang}: {exc}")
            outputs[lang] = f"(failed)"

    # Generate summary index HTML
    summary_lines = [
        "# P5.13 Multi-Language Poster Summary",
        "",
        f"- Source: `{args.image}`",
        f"- Style: `{args.style}` / Layout: `{args.layout}`",
        f"- Enhance: `{args.enhance_preset} @ {args.enhance_strength}`",
        f"- AI Copy: `{args.ai_copy}` / Auto Color: `{args.auto_color}`",
        "",
        "| Language | Output |",
        "| --- | --- |",
    ]
    for lang in args.languages:
        status = outputs.get(lang, "(missing)")
        summary_lines.append(f"| {lang} | `{status}` |")
    if warnings:
        summary_lines.append("")
        summary_lines.append("### Warnings")
        for w in warnings:
            summary_lines.append(f"- {w}")

    summary_path = run_dir / "i18n_summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    result = I18nPosterResult(
        image=str(args.image.resolve()),
        style=args.style,
        layout=args.layout,
        languages=list(args.languages),
        outputs=outputs,
        enhance_preset=args.enhance_preset,
        enhance_strength=args.enhance_strength,
        ai_copy=args.ai_copy,
        auto_color=args.auto_color,
        run_dir=str(run_dir),
        warnings=warnings,
    )

    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

    # Print brief summary
    for lang in args.languages:
        out = outputs.get(lang, "?")
        print(f"  [{lang}] {out}")


if __name__ == "__main__":
    main()
