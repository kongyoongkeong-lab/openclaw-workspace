# Test PDF Input Directory

## Instructions
Place your sample PDF here for Phase 2 Step 2 validation.

## Expected Format
- Any PDF file (scanned or digital)
- Max size: 16MB (sandbox limit)
- Common formats: PDF, PDF/A, scanned images

## Processing Pipeline
```bash
python3 pdf_pipeline.py \
  input/<your_sample.pdf> \
  output/
```

## Example
```bash
# Place your test PDF here
cp ~/Downloads/sample.pdf input/

# Run pipeline
python3 pdf_pipeline.py input/sample.pdf output/
```
