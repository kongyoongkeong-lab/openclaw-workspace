# Reports & Extracted Data

从 PDF 分析中生成的报告和提取的数据集。
通过 GitHub 进行版本控制。

## Structure
```
reports/
├── README.md
└── extracted/          — 从 PDF 中提取的结构化数据（JSON）
```

## Workflow
1. 使用 pdf_processor.py 处理 PDF
2. 使用 `save` 命令将结果保存至此目录
3. 每日自动备份会提交至 GitHub
