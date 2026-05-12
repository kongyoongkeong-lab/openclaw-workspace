#!/usr/bin/env python3
"""
OCR 文本校对助手
- 标出可疑乱码行
- 高亮关键字段
- 生成校对清单
"""

import re

def identify_fields(text):
    """识别关键字段并高亮"""
    patterns = {
        '机构名称': [r'[A-Z]{2,30}', r'Care\s+Centre'],
        '地址': [r'\d+,\s*Taman\s+\w+\s+', r'\d+\s+Jalan\s+\w+'],
        '电话': [r'\d{3}-\d{4}', r'\d{4}'],
        '邮箱': [r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'],
    }
    highlighted = text
    matches = {}
    
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches[field] = re.findall(pattern, text)
            if matches[field]:
                highlighted += f"\n【{field}】: {matches[field]}"
    
    return highlighted, matches

def flag_uncertain(text):
    """标记可疑乱码行"""
    uncertain = []
    certain = []
    
    for i, line in enumerate(text.split('\n')):
        # 简单启发式：只含字母数字 + 部分标点 = 可能有效
        # 连续非字母数字字符 > 3 = 可能乱码
        if re.match(r'^[\w\s,.-]+$', line.strip()):
            certain.append(f"[OK] {line}")
        else:
            uncertain.append(f"[?] {line}")
    
    return uncertain, certain

def generate_review_report(input_path, output_path):
    """生成校对报告"""
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    highlighted, matches = identify_fields(text)
    uncertain, certain = flag_uncertain(text)
    
    report = []
    report.append("=" * 60)
    report.append("OCR 校对报告")
    report.append("=" * 60)
    report.append(f"\n📄 输入文件：{input_path}")
    report.append(f"📊 总行数：{len(text.split(chr(10)))}")
    report.append(f"✅ 可能有效：{len(certain)} 行")
    report.append(f"⚠️  可疑乱码：{len(uncertain)} 行")
    
    report.append("\n🔍 已识别关键字段:")
    for field, items in matches.items():
        if items:
            report.append(f"  【{field}】: {', '.join(items)}")
    
    report.append("\n⚠️  可疑乱码行:")
    for line in uncertain:
        report.append(f"  {line}")
    
    report.append("\n✅ 可能有效行:")
    for line in certain[:20]:  # 只显示前 20 行
        report.append(f"  {line}")
    
    report.append("\n" + "=" * 60)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print("✅ 校对报告已生成:", output_path)
    return '\n'.join(report)

if __name__ == "__main__":
    input_file = "/home/jason2ykk/.openclaw/workspace/extracted_text_ocr_highres.txt"
    output_file = "/home/jason2ykk/.openclaw/workspace/ocr_review_report.txt"
    
    print("=" * 60)
    print("OCR 校对分析")
    print("=" * 60)
    print()
    
    try:
        report = generate_review_report(input_file, output_file)
        print(report)
    except FileNotFoundError as e:
        print(f"❌ 文件未找到：{e}")
