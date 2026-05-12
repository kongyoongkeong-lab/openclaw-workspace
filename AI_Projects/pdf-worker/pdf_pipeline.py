#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2: CPU Utility Layer - PDF/OCR Worker Pipeline
"""

import os
import re
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageOps
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")
PROCESSING_DIR = os.path.join(BASE_DIR, "processing")
COMPLETED_DIR = os.path.join(BASE_DIR, "completed")
FAILED_DIR = os.path.join(BASE_DIR, "failed")
CACHE_DIR = os.path.join(BASE_DIR, "cache")

def preprocess_image(img, target_size=(1024, 1024)):
    """
    Resize, crop, denoise, grayscale preprocessing
    """
    img = img.convert("RGB")
    
    # Resize to target size
    img_resized = img.resize((target_size[0], target_size[1]), Image.LANCZOS)
    
    # Grayscale
    img_gray = img_resized.convert("L")
    
    # Denoise with simple Gaussian
    img = Image.fromarray(np.array(img_gray))
    img = img.filter(ImageFilter.GaussianBlur(radius=1))
    
    return img_gray

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using PyMuPDF + OCR fallback
    """
    doc = fitz.open(pdf_path)
    text = ""
    
    for page in doc:
        text += page.get_text("text")
    
    # If little text detected, trigger OCR
    if len(text.strip()) < 50:
        images = convert_from_path(pdf_path)
        full_text = ""
        for img in images:
            preprocessed = preprocess_image(img)
            ocr_text = pytesseract.image_to_string(preprocessed)
            full_text += ocr_text
        
        return full_text if len(full_text.strip()) > 0 else "No text detected (empty PDF)"
    
    return text

if __name__ == "__main__":
    print("✓ Phase 2: CPU Utility Layer - PDF Pipeline Initialized")
    print(f"✓ Input: {INPUT_DIR}")
    print(f"✓ Output: {COMPLETED_DIR}")
    print(f"✓ Fallback: {FAILED_DIR}")
    print("\nReady for test file.")
