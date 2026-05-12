#!/usr/bin/env python3
"""
Generate a multi-page test PDF for pipeline validation
Phase 2 Step 2 - Test Data Generation
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

import os

def create_test_pdf(output_path: str):
    """Create a multi-page test PDF with text and tables"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Page 1: Text content
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-50, "Test PDF for OCR Validation")
    
    c.setFont("Helvetica", 12)
    text = """
This is a test PDF containing various elements for OCR pipeline validation.

Page 1: Text Content
====================
Welcome to the OpenClaw PDF Processing Pipeline.

This document contains:
- Plain text paragraphs
- Numbered lists
- Technical specifications
- Table data
- Charts and diagrams (simulated)

Purpose:
- Validate OCR extraction
- Test text preprocessing
- Verify table recognition
- Check image processing
- Measure processing speed
"""
    y = height - 120
    for line in text.split('\n'):
        if len(line) > 60:
            c.drawString(50, y, line[:57] + "...")
            y -= 12
        else:
            c.drawString(50, y, line)
            y -= 12
    
    c.showPage()
    
    # Page 2: Table content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height-50, "Sample Data Table")
    
    c.setFont("Helvetica", 10)
    y = height - 100
    
    # Table headers
    headers = ["ID", "Name", "Value", "Status", "Timestamp"]
    for i, header in enumerate(headers):
        c.drawString(50 + i*100, y, header)
    
    y -= 20
    
    # Table data
    data = [
        ["001", "Test Item A", "123.45", "Active", "2026-05-12 18:00:00"],
        ["002", "Test Item B", "234.56", "Active", "2026-05-12 18:05:00"],
        ["003", "Test Item C", "345.67", "Pending", "2026-05-12 18:10:00"],
        ["004", "Test Item D", "456.78", "Completed", "2026-05-12 18:15:00"],
        ["005", "Test Item E", "567.89", "Active", "2026-05-12 18:20:00"],
    ]
    
    for row in data:
        for i, value in enumerate(row):
            c.drawString(50 + i*100, y, str(value))
        y -= 18
    
    c.showPage()
    
    # Page 3: Lists and mixed content
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height-50, "Lists and Mixed Content")
    
    c.setFont("Helvetica", 12)
    y = height - 100
    
    c.drawString(50, y, "Numbered List:")
    y -= 20
    for i in range(1, 6):
        c.drawString(70, y, f"{i}. This is list item number {i} for testing.")
        y -= 18
    
    y -= 20
    c.drawString(50, y, "Bulleted List:")
    y -= 20
    for i in range(1, 6):
        c.drawString(70, y, f"• Item {i}: Testing bullet point extraction")
        y -= 18
    
    c.showPage()
    
    # Page 4: Conclusion
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-50, "Processing Complete")
    
    c.setFont("Helvetica", 12)
    y = height - 120
    text = """
This test PDF has been successfully generated.

Pipeline Validation Checklist:
[✓] Text extraction
[✓] Table recognition
[✓] List parsing
[✓] OCR validation
[✓] Page structure detection

The PDF is ready for OCR + preprocessing pipeline testing.

End of Test Document.
"""
    for line in text.split('\n'):
        if line.strip():
            c.drawString(50, y, line)
            y -= 14
    
    c.save()
    print(f"[*] Test PDF created: {output_path}")
    print(f"    Pages: 4")
    print(f"    Content: Text, Tables, Lists")
    
    return output_path

if __name__ == "__main__":
    output_path = "/home/jason2ykk/.openclaw/workspace/pdf-test/input/test_sample.pdf"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    create_test_pdf(output_path)
    print(f"\n[+] Test PDF ready: {output_path}")
