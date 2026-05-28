#!/usr/bin/env python3
"""Run a local PDF handling quality gate.

The gate creates synthetic fixtures in /tmp, runs the PDF intake tool, and
checks the core local PDF stack. Use --strict to fail when recommended system
PDF binaries are missing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


ROOT = Path(__file__).resolve().parents[1]
PDF_INTAKE = ROOT / "tools" / "pdf_intake.py"
RECOMMENDED_BINARIES = ["pdfinfo", "pdftotext", "pdfimages", "qpdf", "gs", "tesseract"]


def run(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)


def make_text_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("OpenClaw PDF Quality Gate", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Digital text extraction target. Total amount 12345.", styles["Normal"]),
    ]
    doc.build(story)


def make_table_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    data = [["Item", "Count", "Status"], ["Text", "1", "OK"], ["Table", "2", "OK"]]
    table = Table(data)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([table])


def make_encrypted_pdf(source: Path, target: Path) -> None:
    reader = PdfReader(str(source))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("openclaw-test")
    with target.open("wb") as handle:
        writer.write(handle)


def make_malformed_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.7\nthis is intentionally truncated\n")


def make_scanned_pdf(path: Path, tmpdir: Path) -> None:
    img = Image.new("RGB", (1000, 500), "white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 200), "OpenClaw scanned OCR target", fill="black")
    image_path = tmpdir / "scanned_source.png"
    img.save(image_path)
    image = Image.open(image_path).convert("RGB")
    image.save(path, "PDF")


def intake(path: Path) -> dict[str, Any]:
    completed = run([sys.executable, str(PDF_INTAKE), str(path), "--pretty"])
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {"ok": False, "error": "invalid_json", "stdout": completed.stdout, "stderr": completed.stderr}
    payload["_returncode"] = completed.returncode
    return payload


def test_pdfplumber(path: Path) -> dict[str, Any]:
    try:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return {"ok": "OpenClaw PDF Quality Gate" in text, "chars": len(text)}
    except Exception as exc:  # noqa: BLE001 - gate must serialize failures.
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}"}


def test_camelot(path: Path) -> dict[str, Any]:
    try:
        import camelot

        tables = camelot.read_pdf(str(path), pages="1", flavor="stream")
        return {"ok": len(tables) > 0, "tables": len(tables)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}"}


def test_pdf2image(path: Path) -> dict[str, Any]:
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(path), first_page=1, last_page=1, dpi=100)
        return {"ok": bool(images), "images": len(images)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PDF handling capability checks.")
    parser.add_argument("--strict", action="store_true", help="Fail if recommended system binaries are missing.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="openclaw-pdf-gate-") as raw_tmp:
        tmpdir = Path(raw_tmp)
        text_pdf = tmpdir / "text.pdf"
        table_pdf = tmpdir / "table.pdf"
        encrypted_pdf = tmpdir / "encrypted.pdf"
        malformed_pdf = tmpdir / "malformed.pdf"
        scanned_pdf = tmpdir / "scanned.pdf"

        make_text_pdf(text_pdf)
        make_table_pdf(table_pdf)
        make_encrypted_pdf(text_pdf, encrypted_pdf)
        make_malformed_pdf(malformed_pdf)
        make_scanned_pdf(scanned_pdf, tmpdir)

        dependencies = {name: shutil.which(name) is not None for name in RECOMMENDED_BINARIES}
        checks: dict[str, Any] = {
            "dependencies": dependencies,
            "intake_text_pdf": intake(text_pdf),
            "intake_table_pdf": intake(table_pdf),
            "intake_encrypted_pdf": intake(encrypted_pdf),
            "intake_malformed_pdf": intake(malformed_pdf),
            "intake_scanned_pdf": intake(scanned_pdf),
            "pdfplumber_text": test_pdfplumber(text_pdf),
            "camelot_table": test_camelot(table_pdf),
            "pdf2image_scanned": test_pdf2image(scanned_pdf),
        }

    required_passes = [
        checks["intake_text_pdf"].get("ok") is True,
        checks["intake_table_pdf"].get("ok") is True,
        checks["intake_encrypted_pdf"].get("recommended_route") == "needs_password_or_decrypt",
        checks["intake_malformed_pdf"].get("ok") is False,
        checks["pdfplumber_text"].get("ok") is True,
        checks["camelot_table"].get("ok") is True,
    ]
    missing_bins = [name for name, ok in dependencies.items() if not ok]
    checks["summary"] = {
        "core_pass": all(required_passes),
        "strict_pass": all(required_passes) and not missing_bins,
        "missing_recommended_binaries": missing_bins,
        "ocr_ready": checks["pdf2image_scanned"].get("ok") is True and dependencies.get("tesseract", False),
    }

    print(json.dumps(checks, indent=2 if args.pretty else None, sort_keys=True))
    if args.strict:
        return 0 if checks["summary"]["strict_pass"] else 2
    return 0 if checks["summary"]["core_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
