#!/usr/bin/env python3
"""P5.14 Batch poster generation.

Processes multiple images through the full P5.9 pipeline.
Each image gets routed, enhanced, rendered, scored, and auto-selected.
Outputs a batch summary index with per-image results.
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

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass
class BatchResult:
    run_dir: str
    total: int
    succeeded: int
    failed: int
    items: dict[str, dict[str, Any]]
    summary: str


def run_single(
    image: Path,
    topic_hint: str,
    allow_p54: bool,
    output_dir: Path,
    timeout: int = 480,
) -> dict[str, Any]:
    """Run the P5.9 pipeline for a single image."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / image.stem.replace(" ", "_")[:60]
    run_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(ROOT / "tools/make_poster.py"),
        "--image", str(image),
        "--output-dir", str(run_dir),
    ]
    if topic_hint:
        cmd.extend(["--hint", topic_hint])
    if allow_p54:
        cmd.append("--allow-p54")

    start = datetime.now()
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False, timeout=timeout)
    elapsed = (datetime.now() - start).total_seconds()

    if proc.returncode == 0:
        manifest_path = run_dir / "make_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            manifest = {"error": "make_manifest.json not created"}
        return {
            "image": str(image),
            "status": "success",
            "elapsed_s": round(elapsed, 1),
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()[:200],
            "manifest": manifest,
            "decision": manifest.get("decision", "unknown"),
            "style": manifest.get("route", {}).get("style", "?"),
            "selected": manifest.get("selected_image", ""),
        }

    return {
        "image": str(image),
        "status": "failed",
        "elapsed_s": round(elapsed, 1),
        "stdout": proc.stdout.strip()[:300],
        "stderr": proc.stderr.strip()[:300],
        "manifest": None,
        "decision": "failed",
        "style": "?",
        "selected": "",
    }


def collect_images(paths: list[Path], directory: Path | None) -> list[Path]:
    """Collect image files from CLI paths and/or directory."""
    seen = set()
    images: list[Path] = []
    for p in paths:
        resolved = p.resolve()
        if resolved.exists() and resolved.suffix.lower() in SUPPORTED_EXTENSIONS and resolved not in seen:
            images.append(resolved)
            seen.add(resolved)
    if directory:
        for item in sorted(directory.iterdir()):
            if item.suffix.lower() in SUPPORTED_EXTENSIONS and item not in seen:
                images.append(item.resolve())
                seen.add(item)
    return images


def write_summary_html(items: list[dict[str, Any]], output: Path) -> None:
    """Write a simple HTML summary for quick visual review."""
    rows = []
    for item in items:
        status_color = "#e8f5e9" if item["status"] == "success" else "#ffebee"
        selected = item.get("selected", "")
        img_tag = (
            f'<img src="{selected}" width="280" style="border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.15)"/>'
            if selected and Path(selected).exists()
            else "(no image)"
        )
        rows.append(f"""
        <tr style="background:{status_color};border-bottom:1px solid #ddd">
          <td style="padding:12px">{Path(item['image']).name}</td>
          <td style="padding:12px">{item['style']}</td>
          <td style="padding:12px">{item['decision']}</td>
          <td style="padding:12px">{item['elapsed_s']}s</td>
          <td style="padding:12px">{img_tag}</td>
        </tr>""")

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"/>
<title>Batch Poster Summary</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1200px; margin: 2rem auto; padding: 0 1rem; background: #faf7f2; color: #2f241c; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,.08); }}
th {{ background: #2f241c; color: #fff7e6; padding: 14px 12px; text-align: left; font-weight: 600; }}
h1 {{ font-size: 28px; }}
.meta {{ color: #6b5c4f; margin-bottom: 2rem; }}
a {{ color: #8b4513; }}
</style></head><body>
<h1>📋 Batch Poster Summary</h1>
<p class="meta">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Total: {len(items)} | Success: {sum(1 for i in items if i['status'] == 'success')} | Failed: {sum(1 for i in items if i['status'] != 'success')}</p>
<table><thead><tr>
<th>Image</th><th>Style</th><th>Decision</th><th>Time</th><th>Preview</th>
</tr></thead><tbody>
{"".join(rows)}
</tbody></table></body></html>"""
    output.write_text(html, encoding="utf-8")
    print(f"summary_html={output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="P5.14 Batch poster generation.")
    parser.add_argument("--images", nargs="*", type=Path, default=[], help="One or more image paths.")
    parser.add_argument("--directory", "-d", type=Path, help="Directory containing images.")
    parser.add_argument("--hint", default="", help="Topic hint for all images (optional).")
    parser.add_argument("--allow-p54", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--max-images", type=int, default=10, help="Limit to N images.")
    parser.add_argument("--timeout", type=int, default=480, help="Timeout per image in seconds.")
    args = parser.parse_args()

    images = collect_images(args.images, args.directory)
    if not images:
        raise SystemExit("No image files found. Pass --images or --directory.")
    images = images[: args.max_images]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (args.output_dir or REPORTS / "batch" / f"batch_poster_{timestamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    items: list[dict[str, Any]] = []
    succeeded = 0
    failed = 0

    for idx, img in enumerate(images, start=1):
        print(f"[{idx}/{len(images)}] Processing: {img.name}")
        result = run_single(img, args.hint, args.allow_p54, run_dir, args.timeout)
        items.append(result)
        if result["status"] == "success":
            succeeded += 1
        else:
            failed += 1

    # Write results.json
    results_path = run_dir / "batch_results.json"
    payload = {
        "run_dir": str(run_dir),
        "timestamp": timestamp,
        "total": len(images),
        "succeeded": succeeded,
        "failed": failed,
        "allow_p54": args.allow_p54,
        "hint": args.hint,
        "items": items,
    }
    results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Write summary.md
    summary_lines = [
        "# P5.14 Batch Poster Summary",
        "",
        f"- Timestamp: `{timestamp}`",
        f"- Total: `{len(images)}` | Succeeded: `{succeeded}` | Failed: `{failed}`",
        f"- Hint: `{args.hint}` | P5.4: `{args.allow_p54}`",
        "",
        "| # | Image | Style | Decision | Time | Selected |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for idx, item in enumerate(items, start=1):
        name = Path(item["image"]).name
        style = item["style"]
        decision = item["decision"]
        elapsed = f"{item['elapsed_s']}s"
        selected = Path(item["selected"]).name if item["selected"] and Path(item["selected"]).exists() else "(none)"
        summary_lines.append(f"| {idx} | `{name}` | `{style}` | `{decision}` | {elapsed} | `{selected}` |")
        if item["status"] == "failed":
            err = (item["stderr"] or item["stdout"])[:120]
            summary_lines.append(f"  | ⚠️ Error: {err}")

    summary_path = run_dir / "batch_summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    # Write summary.html
    html_path = run_dir / "batch_index.html"
    write_summary_html(items, html_path)

    print(f"\nP5.14 done: {succeeded} succeeded, {failed} failed, {len(images)} total")
    print(f"  results:  {results_path}")
    print(f"  summary:  {summary_path}")
    print(f"  html:     {html_path}")


if __name__ == "__main__":
    main()
