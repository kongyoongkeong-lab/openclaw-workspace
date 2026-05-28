# Local Poster Stack GitHub Review

Review date: 2026-05-23

## Current Stack

`Qwen + Python/Pillow` is a good v1 setup for Jason's OpenClaw workflow:

- Fully local poster rendering.
- No Canva API.
- No Photoshop automation.
- Fast enough for Telegram image replies.
- Easy to batch and automate.
- Works with current WSL/Python/Ollama setup.

## GitHub Comparison

### Pillow Direct Rendering

Good for deterministic templates, image processing, rounded cards, shadows, and fixed social sizes.

Evidence:

- Pillow is the standard Python imaging library and has a large GitHub ecosystem: https://github.com/topics/pillow
- Existing poster-style projects use Pillow for direct image generation, for example BeatPrints: https://github.com/TrueMyst/BeatPrints

Assessment: best for current v1.

### HTML/CSS Screenshot Rendering

Good for more polished layout, responsive typography, CSS effects, reusable templates, and easier designer-style maintenance.

Evidence:

- Pageres can capture rendered HTML strings and pages into screenshots: https://github.com/sindresorhus/pageres
- Puppeteer screenshot GitHub Action pattern renders URL or file screenshots: https://github.com/cloudposse-github-actions/screenshot
- Telegram screenshot bot examples use Playwright for screenshot output: https://github.com/alenpaul2001/Web-Screenshot-Bot
- Markdown-to-image projects use React/template rendering for social poster cards: https://github.com/gcui-art/markdown-to-image

Assessment: best v2 renderer.

### HTML/XML to Image/PDF Libraries

Good for document-like output and static layout snapshots.

Evidence:

- PlutoPrint generates PDFs and images from HTML/XML: https://github.com/plutoprint/plutoprint

Assessment: useful later for printable flyers or PDF output.

## Recommended Architecture

Keep v1:

- Qwen for copy JSON.
- Pillow for fast local rendering.
- Telegram returns JPG.

Add v2:

- HTML/CSS template renderer.
- Playwright/Puppeteer local screenshot.
- Templates stored as HTML/CSS files.
- Same Qwen JSON copy contract.

## Improvement Roadmap

1. Add template JSON schema:
   - `title`
   - `subtitle`
   - `body`
   - `badge`
   - `footer`
   - `style`
   - `layout`

2. Add HTML/CSS renderer:
   - Generate `poster.html`.
   - Screenshot with local Playwright at `1080x1620`.
   - Export PNG/JPG.

3. Add image-aware style selection:
   - Use local `llava` to classify image:
     - group photo
     - food stall
     - product
     - event
   - Map to style automatically.

4. Add visual QA:
   - Check output dimensions.
   - Check file size.
   - Optional OCR to verify text appears.
   - Optional thumbnail preview before sending.

5. Add Telegram shortcut:
   - User sends image + "制成海报".
   - Router calls local poster generator automatically.

## Verdict

Current setup is correct for v1.

Best next setup is hybrid local rendering:

`Qwen JSON copy -> Pillow quick renderer OR HTML/CSS Playwright premium renderer -> Telegram JPG`

This keeps privacy and local control while improving design quality.

## P2 Implementation Status

Implemented on 2026-05-23.

- Fast renderer: `tools/local_poster_generator.py`
- Premium renderer: `tools/local_poster_premium.py`
- Premium runtime: `npx playwright screenshot` with local Chromium
- No-sudo Chromium libraries: `vendor/playwright-libs/lib`
- Smoke test output:
  - `reports/smoke_premium_food_poster.jpg`
  - `reports/smoke_premium_teacher_poster.jpg`

Operational rule:

- Use Pillow fast mode for quick Telegram replies.
- Use Playwright premium mode when Jason asks for a more polished or Canva-like poster.
- Continue checking GitHub patterns before major setup decisions or package choices.
