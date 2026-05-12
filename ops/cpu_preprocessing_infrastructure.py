#!/usr/bin/env python3
# ============================================================================
# CPU-side Preprocessing & Utility Infrastructure
# Worker Queue: PDF/OCR | Image Preprocessing | Metadata Extraction
# ============================================================================

import os
import json
import time
import sys
import hashlib
from datetime import datetime
from pathlib import Path

import PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import pytesseract

print("=== CPU Preprocessing Infrastructure ===\n")

# ============================================================================
# 1. QUEUE FOLDER CONFIGURATION
# ============================================================================
QUEUE_FOLDERS = {
    "input":     Path("/input"),
    "processing": Path("/processing"),
    "completed": Path("/completed"),
    "cache":     Path("/cache")
}

# ============================================================================
# 2. IMAGE PREPROCESSING PIPELINE
# ============================================================================
def resize_image(img_path, max_dim=1024, keep_aspect=True):
    """Resize image to max dimension while preserving aspect ratio."""
    img = cv2.imread(img_path)
    if img is None:
        print(f"[WARN] Failed to load image: {img_path}")
        return None
    
    h, w = img.shape[:2]
    if max_dim and (h > max_dim or w > max_dim):
        if keep_aspect:
            new_w = max_dim * w / h
            new_h = max_dim * h / w
            img = cv2.resize(img, (int(new_w), int(new_h)))
    return img

def crop_image(img_path, crop_mode="edges"):
    """Crop image to document-like boundaries."""
    img = cv2.imread(img_path)
    if img is None:
        return None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    coords = cv2.findNonZero(thresh)
    x, y, w, h = cv2.boundingRect(coords)
    
    if w > 0 and h > 0:
        cropped = img[y:y+h, x:x+w]
    else:
        cropped = img.copy()
    
    return cropped

def denoise_image(img, strength=3.0):
    """Apply Gaussian denoising to reduce noise."""
    if len(img.shape) == 2:
        img = cv2.fastNlMeansDenoisingSingle(img, None, strength, 7, 21)
    else:
        img = cv2.fastNlMeansDenoising(img, None, strength)
    return img

def preprocess_image(img_path):
    """Execute full image preprocessing pipeline."""
    print(f"\n[PREPROCESS] Processing: {img_path}")
    
    start_time = time.time()
    
    # Step 1: Resize
    img = resize_image(img_path, max_dim=1024)
    if img is None:
        return None
    
    # Step 2: Crop to document area
    img = crop_image(img_path, crop_mode="edges")
    
    # Step 3: Denoise
    img = denoise_image(img, strength=3.0)
    
    # Save to processing queue
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    output_path = QUEUE_FOLDERS["processing"] / f"img_{timestamp}_{hashlib.md5(img_path.encode()).hexdigest()}.png"
    cv2.imwrite(str(output_path), img)
    
    processing_time = time.time() - start_time
    
    return {
        "source": img_path,
        "output": str(output_path),
        "duration_sec": round(processing_time, 3),
        "preprocessing_steps": ["resize", "crop", "denoise"]
    }

# ============================================================================
# 3. PDF/OCR WORKER
# ============================================================================
def extract_pdf_text(pdf_path):
    """Extract text from PDF using PyMuPDF."""
    print(f"\n[PDF/OCR] Processing: {pdf_path}")
    
    text = ""
    try:
        with PyMuPDF.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {page_num} ---\n{page_text}"
    except Exception as e:
        print(f"[ERROR] PDF extraction failed: {e}")
    
    return text

def extract_pdf_images(pdf_path, output_dir=QUEUE_FOLDERS["cache"]):
    """Extract images from PDF."""
    print(f"\n[PDF/OCR] Extracting images from: {pdf_path}")
    
    images = []
    try:
        with PyMuPDF.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_images = page.get_images()
                if page_images:
                    img_info = page_images[0]
                    xref = img_info[0]
                    img_data = pdf.extract_image(xref)
                    
                    img_name = f"page_{len(images)+1}.png"
                    img_path = output_dir / img_name
                    img_data.save(str(img_path))
                    images.append(str(img_path))
    except Exception as e:
        print(f"[ERROR] Image extraction failed: {e}")
    
    return images

def ocr_process(img_path):
    """Perform OCR on preprocessed image using Tesseract."""
    print(f"\n[OCR] Processing: {img_path}")
    
    start_time = time.time()
    
    try:
        # Tesseract configuration for document reading
        config = '--psm 6 --oem 3 --c vadges=false --c spaceskip=true'
        
        # OCR the image
        text = pytesseract.image_to_string(cv2.imread(img_path), config=config)
        confidence = pytesseract.image_to_string(img_path, config=config, output_type=pytesseract.Output.DICT).get('confidence', 0)
        
        processing_time = time.time() - start_time
        
        return {
            "source": img_path,
            "text": text.strip(),
            "confidence": float(confidence) if confidence else 0,
            "duration_sec": round(processing_time, 3)
        }
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return None

# ============================================================================
# 4. METADATA EXTRACTION LAYER
# ============================================================================
def extract_image_metadata(img_path):
    """Extract EXIF and image properties."""
    print(f"\n[META] Processing: {img_path}")
    
    try:
        img = Image.open(img_path)
        
        metadata = {
            "filename": os.path.basename(img_path),
            "dimensions": {"width": img.width, "height": img.height},
            "format": img.format,
            "mode": img.mode,
            "file_size": os.path.getsize(img_path),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            exif_data = img._getexif()
            if exif_data:
                metadata["exif"] = {k: v for k, v in exif_data.items() if k != 0}
        except:
            pass
        
        return metadata
    except Exception as e:
        print(f"[ERROR] Metadata extraction failed: {e}")
        return None

def extract_pdf_metadata(pdf_path):
    """Extract PDF properties."""
    print(f"\n[META] Processing: {pdf_path}")
    
    try:
        with PyMuPDF.open(pdf_path) as pdf:
            metadata = {
                "filename": os.path.basename(pdf_path),
                "page_count": len(pdf.pages),
                "file_size": os.path.getsize(pdf_path),
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                inf = pdf.info
                metadata["pdf_info"] = {k: v for k, v in inf.items()}
            except:
                pass
            
            try:
                meta = pdf.metadata
                metadata["pdf_metadata"] = {k: v for k, v in meta.items() if k != "Producer"}
            except:
                pass
        
        return metadata
    except Exception as e:
        print(f"[ERROR] PDF metadata extraction failed: {e}")
        return None

# ============================================================================
# 5. WORKER QUEUE MANAGER
# ============================================================================
def process_file_from_queue(queue_dir, output_dir):
    """Main worker loop for processing files from input queue."""
    print(f"\n=== Starting Worker Queue: {queue_dir} ===")
    
    while True:
        try:
            # Get list of files in input queue
            files = list(queue_dir.glob("*"))
            if not files:
                print("Input queue empty. Waiting...")
                time.sleep(1)
                continue
            
            # Process first file (non-image, non-PDF)
            for file_path in files:
                if file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                    filename = file_path.name
                    print(f"\n[WORKER] Queued for processing: {filename}")
                    
                    if file_path.suffix.lower() == '.pdf':
                        # Handle PDF
                        result = {"filename": filename, "type": "pdf"}
                        
                        # Extract text
                        text = extract_pdf_text(str(file_path))
                        result["pdf_text"] = text
                        
                        # Extract images
                        images = extract_pdf_images(str(file_path))
                        result["extracted_images"] = images
                        
                        # Extract metadata
                        meta = extract_pdf_metadata(str(file_path))
                        result["metadata"] = meta
                        
                        # Save result
                        result_path = output_dir / f"result_{filename}"
                        with open(result_path, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        print(f"[WORKER] Completed: {filename}")
                        
                    elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                        # Handle images
                        result = {"filename": filename, "type": "image"}
                        
                        # Preprocess image
                        proc_result = preprocess_image(str(file_path))
                        if proc_result:
                            result["preprocessed"] = proc_result
                            
                            # OCR the preprocessed image
                            ocr_result = ocr_process(proc_result["output"])
                            result["ocr"] = ocr_result
                            
                            # Extract metadata
                            meta = extract_image_metadata(proc_result["output"])
                            result["metadata"] = meta
                        else:
                            result["error"] = "Preprocessing failed"
                        
                        # Save result
                        result_path = output_dir / f"result_{filename}"
                        with open(result_path, 'w') as f:
                            json.dump(result, f, indent=2)
                        
                        print(f"[WORKER] Completed: {filename}")
                        
                    break
            
        except Exception as e:
            print(f"[ERROR] Worker error: {e}")
            continue

# ============================================================================
# 6. CPU UTILIZATION MONITORING
# ============================================================================
def get_cpu_utilization():
    """Monitor CPU utilization."""
    try:
        import subprocess
        result = subprocess.run(
            ['top', '-bn1'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        # Parse top output for CPU info
        lines = result.stdout.split('\n')
        cpu_lines = [l for l in lines if 'CPU' in l or '%Cpu' in l]
        
        cpu_stats = []
        for line in cpu_lines:
            try:
                parts = line.split()
                if len(parts) >= 2:
                    user_pct = float(parts[1]) if parts[1] else 0
                    sys_pct = float(parts[2]) if parts[2] else 0
                    cpu_stats.append({
                        "user": user_pct,
                        "system": sys_pct,
                        "total": user_pct + sys_pct
                    })
            except:
                continue
        
        return cpu_stats
    except Exception as e:
        print(f"[WARN] CPU monitoring error: {e}")
        return []

# ============================================================================
# 7. WORKFLOW OUTPUT JSON
# ============================================================================
def generate_workflow_output():
    """Generate comprehensive workflow output."""
    workflow = {
        "infrastructure": {
            "queue_folders": {
                "input": str(QUEUE_FOLDERS["input"]),
                "processing": str(QUEUE_FOLDERS["processing"]),
                "completed": str(QUEUE_FOLDERS["completed"]),
                "cache": str(QUEUE_FOLDERS["cache"])
            },
            "dependencies": ["PyMuPDF", "pytesseract", "opencv-python", "Pillow", "pandas"],
            "ocr_engine": "Tesseract OCR",
            "pdf_engine": "PyMuPDF"
        },
        "preprocessing_pipeline": {
            "steps": ["resize", "crop", "denoise"],
            "parameters": {
                "max_dimension": 1024,
                "crop_mode": "edges",
                "denoise_strength": 3.0
            }
        },
        "metadata_extraction": {
            "image_fields": ["filename", "dimensions", "format", "mode", "file_size", "timestamp", "exif"],
            "pdf_fields": ["filename", "page_count", "file_size", "timestamp", "pdf_info", "pdf_metadata"]
        },
        "validation": {
            "cpu_monitoring": True,
            "error_handling": "try-except with continue",
            "queue_processing": "non-blocking worker loop"
        }
    }
    
    return workflow

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    try:
        # Generate and display workflow output
        print("=== Generated Preprocessing Workflow JSON ===")
        workflow = generate_workflow_output()
        print(json.dumps(workflow, indent=2))
        
        # CPU monitoring
        print("\n=== CPU Utilization Check ===")
        cpu_stats = get_cpu_utilization()
        
        if cpu_stats:
            recent = cpu_stats[-1]
            print(f"\nRecent CPU Stats:")
            print(f"  User: {recent.get('user', 0):.2f}%")
            print(f"  System: {recent.get('system', 0):.2f}%")
            print(f"  Total: {recent.get('total', 0):.2f}%")
            
            # GPU check if available
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"\nGPU Status Available (nvidia-smi)")
                    print(result.stdout[:500])
            except:
                print("\nGPU monitoring not available")
        else:
            print("\nCPU monitoring not available")
        
        print("\n=== Infrastructure Setup Complete ===")
        print(f"\nQueue Folders:")
        for name, path in QUEUE_FOLDERS.items():
            exists = path.exists()
            print(f"  [{name.upper()}]: {path.absolute()} {'[EXISTS]' if exists else '[NEW]'}")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR]: {e}")
        sys.exit(1)
