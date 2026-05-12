#!/usr/bin/env python3
"""
PDF OCR + Preprocessing Pipeline
Phase 2 Step 2 - Test Execution
"""
import sys
import re
from pathlib import Path
import fitz  # PyMuPDF
import tempfile

def extract_text_from_pdf(pdf_path: str) -> list:
    """Extract text from PDF using PyMuPDF"""
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        images = page.get_images(full=True)
        
        page_data = {
            "page": page_num,
            "text": text,
            "word_count": len(text.split()),
            "image_count": len(images)
        }
        pages.append(page_data)
    
    doc.close()
    return pages

def run_pipeline(pdf_path: str, output_dir: str) -> dict:
    """Main pipeline execution"""
    print(f"[*] Processing: {pdf_path}")
    
    if not Path(pdf_path).exists():
        print("[!] ERROR: PDF file not found")
        return {"status": "error", "message": "PDF not found"}
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        pages = extract_text_from_pdf(pdf_path)
        
        # Save extracted text
        text_file = output_dir / "extracted_text.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            for page in pages:
                f.write(f"=== Page {page['page']} ===\n")
                f.write(page["text"] + "\n\n")
        
        result = {
            "status": "success",
            "pages_processed": len(pages),
            "total_words": sum(p["word_count"] for p in pages),
            "output_file": str(text_file)
        }
        
        print(f"[+] Completed: {result['pages_processed']} pages, {result['total_words']} words")
        return result
        
    except Exception as e:
        print(f"[!] ERROR: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: pdf_pipeline.py <input_pdf> <output_dir>")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_dir = sys.argv[2]
    
    result = run_pipeline(input_pdf, output_dir)
    
    import json
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)
