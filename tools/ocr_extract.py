#!/usr/bin/env python3
"""PDF OCR 提取 - 方案 1"""

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def extract_with_ocr(pdf_path, output_path=None):
    """使用 OCR 提取 PDF 文本"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        print(f"📄 共 {len(doc)} 页")
        
        for i, page in enumerate(doc):
            print(f"  正在处理第 {i+1} 页...")
            # 转为高分辨率图像
            pix = page.get_pixmap(matrix=fitz.Matrix(2))
            img_path = f"/home/jason2ykk/.openclaw/workspace/temp_page_{i}.png"
            pix.save(img_path)
            
            # OCR
            img = Image.open(img_path)
            page_text = pytesseract.image_to_string(img)
            text += page_text
            print(f"  ✅ 第 {i+1} 页完成")
        
        doc.close()
        
        # 保存
        if output_path:
            with open(output_path, "w") as f:
                f.write(text)
            print(f"\n✅ OCR 完成！文本已保存到：{output_path}")
            print(f"   共 {len(text)} 字符")
        
        return text
        
    except ImportError as e:
        print(f"❌ 缺失依赖：{e}")
        print("   请运行：pip install pytesseract pillow")
        print("   并确保已安装：sudo apt install tesseract-ocr")
        return None

if __name__ == "__main__":
    pdf_file = "/home/jason2ykk/.openclaw/workspace/100---fe516ca0-a02f-465c-b585-3b1150271a90.pdf"
    output = "/home/jason2ykk/.openclaw/workspace/extracted_text_ocr.txt"
    
    print("=" * 60)
    print("PDF OCR 文本提取")
    print("=" * 60 + "\n")
    
    result = extract_with_ocr(pdf_file, output)
    
    if result:
        print("\n" + "=" * 60)
        print("✅ 提取成功！")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 提取失败（依赖缺失）")
        print("=" * 60)
        print("\n请手动安装：sudo apt install tesseract-ocr")
