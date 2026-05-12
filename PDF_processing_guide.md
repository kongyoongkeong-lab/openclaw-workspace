# PDF 处理完整指南

## 📄 文件名
`100---fe516ca0-a02f-465c-b585-3b1150271a90.pdf`

---

## ✅ 步骤 1: 移动文件到 Workspace

```bash
mv /home/jason2ykk/.openclaw/media/inbound/100---fe516ca0-a02f-465c-b585-3b1150271a90.pdf \
   /home/jason2ykk/.openclaw/workspace/
```

**确认**:
```bash
ls -lh /home/jason2ykk/.openclaw/workspace/*.pdf
```

---

## ✅ 步骤 2: 安装 PyMuPDF

```bash
pip install --upgrade PyMuPDF
```

**确认安装**:
```bash
python3 -c "import fitz; print('PyMuPDF 已安装，版本:', fitz.version)"
```

---

## ✅ 步骤 3: 执行文本提取

```bash
python3 /home/jason2ykk/.openclaw/workspace/tools/pdf_processor.py \
   /home/jason2ykk/.openclaw/workspace/100---fe516ca0-a02f-465c-b585-3b1150271a90.pdf
```

---

## ✅ 步骤 4 (可选): 批量处理

```bash
# 处理当前目录所有 PDF
for f in /home/jason2ykk/.openclaw/workspace/*.pdf; do
    pdf_file=$(basename "$f" .pdf)
    echo "Processing $pdf_file.pdf"
    python3 /home/jason2ykk/.openclaw/workspace/tools/pdf_processor.py "$f" > "/home/jason2ykk/.openclaw/workspace/${pdf_file}.txt"
done

# 显示结果
ls -lh /home/jason2ykk/.openclaw/workspace/*.txt
```

---

## 🤖 Pentagon Team 状态

- **@intel (Research)**: PDF 分析待启动
- **@ops (Execution)**: 命令待执行
- **@sentinel (Guardian)**: 安全监控中

---

**执行以上命令后**，我将为您提取 PDF 内容并分析。
