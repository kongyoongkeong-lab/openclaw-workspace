#!/usr/bin/env python3
"""Preflight and route PDF files before extraction/summarization.

The script is intentionally conservative: it does not send content to any API,
does not write outside optional output paths, and returns structured JSON that
other OpenClaw tools can use for routing decisions.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_MAX_MB = 100.0
DEFAULT_MAX_PAGES = 500
TEXT_SAMPLE_PAGES = 3
MIN_TEXT_CHARS_PER_PAGE = 25

SENSITIVE_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"),
    "iban_like": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b", re.I),
    "credit_card_like": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "invoice": re.compile(r"\b(invoice|receipt|tax|bank|account|passport|identity|contract|confidential)\b", re.I),
}


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(args: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "available": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    except FileNotFoundError:
        return {"available": False, "error": "missing_binary"}
    except subprocess.TimeoutExpired:
        return {"available": True, "error": "timeout"}


def file_signature(path: Path) -> dict[str, Any]:
    data = path.read_bytes()[:8]
    result: dict[str, Any] = {
        "magic_bytes_hex": data.hex(),
        "has_pdf_header": data.startswith(b"%PDF-"),
    }
    if command_exists("file"):
        result["file"] = run_command(["file", "--brief", "--mime-type", str(path)], timeout=5)
    return result


def inspect_with_pymupdf(path: Path, sample_pages: int) -> dict[str, Any]:
    import fitz  # PyMuPDF

    started = time.monotonic()
    doc = fitz.open(str(path))
    text_parts: list[str] = []
    page_count = doc.page_count
    encrypted = bool(doc.is_encrypted)

    if not encrypted:
        for index in range(min(sample_pages, page_count)):
            text_parts.append(doc[index].get_text("text") or "")

    sample_text = "\n".join(text_parts)
    return {
        "ok": True,
        "engine": "pymupdf",
        "pages": page_count,
        "encrypted": encrypted,
        "sample_text_chars": len(sample_text),
        "sample_text": sample_text[:2000],
        "seconds": round(time.monotonic() - started, 4),
    }


def classify_privacy(text: str) -> dict[str, Any]:
    hits = []
    for name, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            hits.append(name)
    if not text:
        level = "unknown"
    elif hits:
        level = "sensitive"
    else:
        level = "low"
    return {"level": level, "signals": hits}


def recommend_route(
    *,
    ok: bool,
    encrypted: bool,
    pages: int | None,
    needs_ocr: bool,
    privacy_level: str,
    size_mb: float,
    max_pages: int,
    max_mb: float,
) -> str:
    if not ok:
        return "reject_invalid_pdf"
    if encrypted:
        return "needs_password_or_decrypt"
    if size_mb > max_mb or (pages is not None and pages > max_pages):
        return "needs_user_confirmation_large_pdf"
    if privacy_level in {"sensitive", "unknown"}:
        return "local_only"
    if needs_ocr:
        return "local_ocr"
    return "local_text_then_optional_api_summary"


def inspect_pdf(path: Path, max_mb: float, max_pages: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "path": str(path),
        "dependencies": {
            "file": command_exists("file"),
            "pdfinfo": command_exists("pdfinfo"),
            "pdftotext": command_exists("pdftotext"),
            "pdfimages": command_exists("pdfimages"),
            "qpdf": command_exists("qpdf"),
            "ghostscript": command_exists("gs"),
            "tesseract": command_exists("tesseract"),
        },
        "limits": {"max_mb": max_mb, "max_pages": max_pages},
        "warnings": [],
    }

    if not path.exists():
        result["error"] = "file_not_found"
        return result
    if not path.is_file():
        result["error"] = "not_a_file"
        return result

    size_mb = path.stat().st_size / (1024 * 1024)
    result["size_mb"] = round(size_mb, 4)
    result["signature"] = file_signature(path)
    if not result["signature"]["has_pdf_header"]:
        result["error"] = "missing_pdf_header"
        return result

    if command_exists("qpdf"):
        result["qpdf_check"] = run_command(["qpdf", "--check", str(path)], timeout=15)
    else:
        result["warnings"].append("qpdf_missing_validation_limited")

    try:
        inspection = inspect_with_pymupdf(path, TEXT_SAMPLE_PAGES)
        result["inspection"] = {k: v for k, v in inspection.items() if k != "sample_text"}
        sample_text = inspection["sample_text"]
    except Exception as exc:  # noqa: BLE001 - audit tool must serialize failures.
        result["error"] = f"pymupdf_error:{type(exc).__name__}:{exc}"
        return result

    pages = int(result["inspection"]["pages"])
    encrypted = bool(result["inspection"]["encrypted"])
    text_chars = int(result["inspection"]["sample_text_chars"])
    needs_ocr = (not encrypted) and pages > 0 and text_chars < min(pages, TEXT_SAMPLE_PAGES) * MIN_TEXT_CHARS_PER_PAGE
    privacy = classify_privacy(sample_text)

    if needs_ocr and not command_exists("pdfinfo"):
        result["warnings"].append("poppler_missing_ocr_rendering_blocked")
    if needs_ocr and not command_exists("tesseract"):
        result["warnings"].append("tesseract_missing_ocr_blocked")
    if size_mb > max_mb:
        result["warnings"].append("file_exceeds_size_limit")
    if pages > max_pages:
        result["warnings"].append("file_exceeds_page_limit")

    result.update(
        {
            "ok": True,
            "pages": pages,
            "encrypted": encrypted,
            "has_extractable_text": text_chars >= min(pages, TEXT_SAMPLE_PAGES) * MIN_TEXT_CHARS_PER_PAGE,
            "needs_ocr": needs_ocr,
            "privacy": privacy,
            "recommended_route": recommend_route(
                ok=True,
                encrypted=encrypted,
                pages=pages,
                needs_ocr=needs_ocr,
                privacy_level=privacy["level"],
                size_mb=size_mb,
                max_pages=max_pages,
                max_mb=max_mb,
            ),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight and route a PDF file.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args()

    result = inspect_pdf(Path(args.pdf).expanduser().resolve(), args.max_mb, args.max_pages)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
