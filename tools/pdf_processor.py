#!/usr/bin/env python3
"""PDF 处理工具 - Pentagon Team 本地方案"""

import fitz  # PyMuPDF
import sys

def extract_text(pdf_path):
    """提取 PDF 文本内容"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"错误：{e}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        print(extract_text(pdf_file))
    else:
        print("用法：python pdf_processor.py <pdf 文件路径>")
