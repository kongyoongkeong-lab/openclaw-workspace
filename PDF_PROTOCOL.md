# 📄 PDF Processing Protocol — v1

**Engine:** pypdf (Python) + OpenClaw `pdf` tool
**Storage:** Local workspace + GitHub versioned reports
**Updated:** 2026-05-22

## Pipeline

```
User request ("extract table from PDF", "merge these PDFs", etc.)
  │
  ▼
┌──────────────────────────────────────┐
│ 1. FILE ACQUISITION                   │
│    - Local: file_fetch(path)          │
│    - Web: web_fetch/curl PDF from URL │
│    - GitHub: gh api to download       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 2. PROCESS                            │ ← pdf_processor.py
│    - Extract text                     │
│    - Extract tables (by row/col)      │
│    - Merge/split documents            │
│    - Read metadata (author, pages)    │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 3. ANALYZE                            │ ← @intel (if needed)
│    - Summarize content                │
│    - Cross-reference with web/GitHub  │
│    - Extract key data points          │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 4. OUTPUT                             │
│    - Return extracted text to @main   │
│    - Save processed JSON to workspace │
│    - Optionally commit to GitHub      │
└──────────────────────────────────────┘
```

## GitHub Integration

### Report Storage

Generated reports and extracted data can be stored in GitHub:

```
reports/
├── README.md
├── 2026-05-22_system_audit.md
├── 2026-05-21_daily_pulse.md
└── extracted/
    ├── 2026-05-22_paper_analysis.json
    └── 2026-05-20_invoice_data.json
```

### What Gets Committed

| Data | GitHub? | Format | Size Limit |
|------|---------|--------|------------|
| Extracted text summaries | ✅ Yes | .md | Reasonable |
| Extracted structured data | ✅ Yes | .json | Reasonable |
| Generated reports | ✅ Yes | .md | Reasonable |
| PDF templates/forms | ✅ Yes | .pdf | < 5MB |
| Source PDFs (large) | ❌ No | - | Too large |
| Binary PDF attachments | ❌ No | - | Ephemeral |

## Tools

### OpenClaw `pdf` Tool (built-in)

```python
# Analyze a single PDF
pdf("document.pdf", prompt="Extract all tables from this PDF")

# Analyze multiple PDFs
pdf("doc1.pdf", "doc2.pdf", prompt="Compare these two documents")
```

### `pdf_processor.py` (custom)

```bash
python3 ~/openclaw-stack/pdf_processor.py extract document.pdf
python3 ~/openclaw-stack/pdf_processor.py merge doc1.pdf doc2.pdf -o merged.pdf
python3 ~/openclaw-stack/pdf_processor.py split document.pdf -o pages/
python3 ~/openclaw-stack/pdf_processor.py metadata document.pdf
```

### pypdf (Python library)

```python
from pypdf import PdfReader, PdfWriter

# Read
reader = PdfReader("file.pdf")
text = reader.pages[0].extract_text()

# Write
writer = PdfWriter()
writer.add_page(reader.pages[0])
writer.write("output.pdf")
```

## Processing Steps

### 1. Text Extraction

```python
def extract_text(path: str) -> str:
    """Extract all text from a PDF."""
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n\n".join(text)
```

### 2. Metadata Extraction

```python
def get_metadata(path: str) -> dict:
    """Extract PDF metadata."""
    reader = PdfReader(path)
    return {
        "pages": len(reader.pages),
        "metadata": reader.metadata,
    }
```

### 3. Merge PDFs

```python
def merge_pdfs(paths: list[str], output: str):
    """Merge multiple PDFs into one."""
    writer = PdfWriter()
    for path in paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with open(output, "wb") as f:
        writer.write(f)
```

### 4. Save Extracted Data to GitHub

```python
def save_to_repo(data: dict, filename: str):
    """Save extracted data to reports/ and commit."""
    path = f"reports/extracted/{filename}"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    # git add + commit handled by auto-backup
```

## Result Format

```markdown
### PDF Analysis — {filename}

**Pages:** {n}
**Author:** {author}
**Created:** {date}

### Summary
{2-3 sentence overview}

### Key Data Points
- {point 1}
- {point 2}

### Full Text
```text
{extracted content}
```
```

## Guardrails

- **Size Limit:** OpenClaw `pdf` tool handles up to 10MB per file
- **Binary PDFs:** Scanned/image-only PDFs may have no extractable text — use OCR as alternative
- **GitHub:** Never commit API keys or credentials found inside PDFs
- **Privacy:** Scan extracted text for PII before committing to GitHub
