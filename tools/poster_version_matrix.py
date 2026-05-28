#!/usr/bin/env python3
"""Generate and rank local poster variants.

P5.6 wraps the existing renderer instead of changing it:
- V6.2 natural documentary mode
- P5.3 polished natural mode
- V3 strong food-cover mode
- optional P5.4 upscale-first mode

Outputs are grouped under reports/matrix/<run-id>/ with a JSON score file,
Markdown report, and comparison contact sheet.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poster_quality_gate import score_image


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FONT_BOLD = ROOT / "assets/fonts/NotoSansCJKsc-Bold.otf"
FONT_REG = ROOT / "assets/fonts/NotoSansCJKsc-Regular.otf"


@dataclass(frozen=True)
class Variant:
    name: str
    layout: str
    enhance_preset: str | None
    enhance_strength: float | None
    note: str


VARIANTS = [
    Variant("p53", "natural-cover", "p53", 0.48, "polished natural default"),
    Variant("v62", "natural-cover", "soft", 0.45, "maximum documentary realism"),
    Variant("v3", "story-cover", "food", 0.80, "strong food/product impact"),
]


def run_command(cmd: list[str], cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False, timeout=180)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{combined}")


def render_variant(image: Path, output: Path, variant: Variant, style: str, auto_photo_position: bool, ai_copy: bool = False, auto_color: bool = False) -> None:
    cmd = [
        sys.executable,
        str(ROOT / "tools/local_poster_premium.py"),
        "--image",
        str(image),
        "--style",
        style,
        "--layout",
        variant.layout,
        "--output",
        str(output),
    ]
    if variant.enhance_preset:
        cmd.extend(
            [
                "--enhance",
                "--enhance-preset",
                variant.enhance_preset,
                "--enhance-strength",
                str(variant.enhance_strength),
            ]
        )
    if auto_photo_position:
        cmd.append("--auto-photo-position")
    if ai_copy:
        cmd.extend(["--ai-copy", "--ai-copy-language", "cn"])
    if auto_color:
        cmd.append("--auto-color")
    run_command(cmd, ROOT)


def render_p54(image: Path, run_dir: Path, style: str, auto_photo_position: bool) -> Path:
    upscaled = run_dir / "p54_upscaled.png"
    output = run_dir / "p54.jpg"
    run_command(
        [
            sys.executable,
            str(ROOT / "tools/comfy_p54_upscale.py"),
            "--image",
            str(image),
            "--output",
            str(upscaled),
            "--max-edge",
            "2600",
        ],
        ROOT,
    )
    render_variant(
        upscaled,
        output,
        Variant("p54", "natural-cover", None, None, "RealESRGAN upscale then natural-cover"),
        style,
        auto_photo_position,
    )
    return output


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError:
        return ImageFont.load_default()


def make_contact_sheet(items: list[dict[str, object]], output: Path) -> None:
    thumb_w, thumb_h = 360, 540
    pad = 24
    label_h = 88
    cols = min(3, max(1, len(items)))
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad), "#f5f1e9")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(FONT_BOLD, 24)
    small_font = _font(FONT_REG, 18)

    for index, item in enumerate(items):
        col = index % cols
        row = index // cols
        x = pad + col * (thumb_w + pad)
        y = pad + row * (thumb_h + label_h + pad)
        with Image.open(str(item["image"])) as src:
            src = src.convert("RGB")
            src.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            px = x + (thumb_w - src.width) // 2
            py = y
            canvas.paste(src, (px, py))
        label_y = y + thumb_h + 10
        draw.text((x, label_y), f"{item['name']}  score {item['score']}", fill="#2f241c", font=title_font)
        draw.text((x, label_y + 34), str(item["recommendation"])[:36], fill="#6b5c4f", font=small_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=92)


def write_report(items: list[dict[str, object]], output: Path, source: Path) -> None:
    lines = [
        "# Poster Version Matrix",
        "",
        f"- Source: `{source}`",
        f"- Best: `{items[0]['name']}` score `{items[0]['score']}`",
        "",
        "| Rank | Version | Score | Grade | Recommendation | Warnings |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for rank, item in enumerate(items, start=1):
        warnings = ", ".join(item.get("warnings", [])) or "none"
        lines.append(
            f"| {rank} | `{item['name']}` | {item['score']} | {item['grade']} | "
            f"{item['recommendation']} | {warnings} |"
        )
    lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and rank local poster variants.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--style", choices=["food", "teacher", "community"], default="food")
    parser.add_argument("--include-p54", action="store_true", help="Run ComfyUI P5.4 upscale variant.")
    parser.add_argument("--auto-photo-position", action="store_true", help="Use face/subject-aware crop positioning.")
    parser.add_argument("--ai-copy", action="store_true", help="Generate copy using local Qwen.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source.")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (args.output_dir or REPORTS / "matrix" / f"poster_matrix_{timestamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[tuple[str, Path, str]] = []
    for variant in VARIANTS:
        output = run_dir / f"{variant.name}.jpg"
        render_variant(args.image.resolve(), output, variant, args.style, args.auto_photo_position, args.ai_copy, args.auto_color)
        outputs.append((variant.name, output, variant.note))

    if args.include_p54:
        output = render_p54(args.image.resolve(), run_dir, args.style, args.auto_photo_position)
        outputs.append(("p54", output, "RealESRGAN upscale then natural-cover"))

    ranked: list[dict[str, object]] = []
    for name, image, note in outputs:
        result = asdict(score_image(image, args.image.resolve(), "natural-cover"))
        result["name"] = name
        result["note"] = note
        ranked.append(result)

    ranked.sort(key=lambda item: (float(item["score"]), float(item["sharpness"])), reverse=True)
    scores_path = run_dir / "scores.json"
    report_path = run_dir / "report.md"
    sheet_path = run_dir / "comparison.jpg"
    scores_path.write_text(json.dumps(ranked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(ranked, report_path, args.image.resolve())
    make_contact_sheet(ranked, sheet_path)

    print(f"best={ranked[0]['name']} score={ranked[0]['score']}")
    print(f"run_dir={run_dir}")
    print(f"report={report_path}")
    print(f"comparison={sheet_path}")


if __name__ == "__main__":
    main()
