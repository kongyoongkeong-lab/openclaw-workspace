---
name: automation-protocol
description: "Automate Chrome CDP, Playwright, Windows file routing, uploads, downloads, and browser-based conversions with verification."
---

# Automation Protocol

Protocol metadata:
- protocol_id: `automation_protocol_skill`
- registry: `../../config/protocol_registry.json`
- risk: medium
- evidence: service used, input path, output path, verification result
- rollback: stop automation and preserve evidence for manual retry

Use this skill for browser or Windows app automation where the goal is to operate a website/app, upload files, download outputs, convert documents, inspect open Chrome tabs, or retry known generation workflows.

Prefer structured control before vision:

1. Existing Chrome CDP tab or dedicated automation Chrome.
2. Playwright locators, DOM text, accessibility roles, keyboard/paste.
3. Direct file input injection for uploads.
4. Browser download events and filesystem verification.
5. Screenshot, OCR, or vision only when structured control fails.

## Safety

- Do not expose API keys, tokens, cookies, or browser session secrets.
- Do not use payment, purchase, account-change, or destructive file actions without explicit Jason confirmation.
- Treat CDP as sensitive local control of a logged-in browser.
- If login is expired, report that manual login is required; do not bypass authentication.
- If a remote service is overloaded, stop repeated retries and report `automation path worked; service failed`.

## Standard Workflow

1. Clarify goal from command, input path, output path, preferred service, and fallback.
2. Locate input using Windows and WSL paths.
3. Attach to Chrome CDP or launch the known automation profile when appropriate.
4. Probe page URL, title, visible text, and available file inputs/buttons.
5. Upload via file input; if the visible button fails, inject into `<input type=file>`.
6. Fill prompt/options using framework-visible events: locator fill, keyboard input, or paste.
7. Submit only after verifying page state changed enough to prove readiness.
8. Monitor progress through DOM text, URL/task ID, download event, or output card.
9. Save/download to the requested location.
10. Verify output path, size greater than zero, modified timestamp, and expected extension.
11. Reply with result, evidence, and any service-side failure reason.

## File Routing

- Windows Desktop: `C:\Users\jason\Desktop`
- OneDrive Desktop: `C:\Users\jason\OneDrive\Desktop`
- Windows documents/project files: `C:\Users\jason\Documents`
- WSL mapping: `/mnt/c/Users/jason/...`
- Large shared input: `/mnt/d/_inbox/`
- Large generated output: `/mnt/d/_outbox/`

Use `scripts/automation_file_probe.py` to find likely inputs and verify outputs.

## Verified Templates

- iLovePDF PDF to PPTX:
  - Tool page: `https://www.ilovepdf.com/pdf_to_powerpoint`
  - Upload PDF, wait for `Convert to PPTX`, click it, wait for download.
  - Verify `.pptx` on Desktop or requested path.
- Canva:
  - Detect open Canva tab and report URL/title.
  - Use Canva connector tools for native design reads/edits when available.
  - Use browser automation only for UI flows the connector cannot handle.
- Gemini and Doubao video generation:
  - Upload image, enter prompt, submit generation.
  - If service returns overload/rate-limit, report service-side failure and do not loop.
  - Preserve prompt, source image path, URL, and visible error text for retry.

## Failure Recovery

- Button not found: read DOM text, inspect roles/selectors, then retry.
- Upload area not clickable: use direct input injection.
- Framework editor ignores text: use keyboard/paste events and verify visible content.
- Download missing: inspect browser downloads, configured download dir, Desktop, and OneDrive Desktop.
- Multiple similar files: prefer newest modified time only after reporting ambiguity if risk is high.
- Output is zero bytes or wrong extension: treat as failed, keep evidence, and choose fallback if available.

## Reporting Contract

Every completed automation task should include:

- Tool/service used.
- Input path.
- Output path.
- File size and modified timestamp when a file is produced.
- Verification result.
- Fallback used or reason no fallback was used.
