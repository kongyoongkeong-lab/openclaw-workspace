# Local Poster Workflow

Purpose: generate Chinese social posters from Telegram photos using the local stack.

## Stack

- Copywriting: optional `ollama run qwen3.5:9b`
- Photo pre-processing: OpenCV + Pillow via `tools/local_photo_enhance.py`
- Fast rendering: Python 3 + Pillow via `tools/local_poster_generator.py`
- Premium rendering: HTML/CSS + local Playwright screenshot via `tools/local_poster_premium.py`
- Quality gate: deterministic image scoring via `tools/poster_quality_gate.py`
- Layout guard: face/subject-safe crop guidance via `tools/poster_layout_guard.py`
- Version matrix: one-shot P5.3/V6.2/V3 comparison via `tools/poster_version_matrix.py`
- Auto-select layer: P5.7 selection manifest via `tools/poster_auto_select.py`
- Route decision layer: P5.8 local image routing via `tools/poster_route_decision.py`
- One-command entrypoint: P5.9 poster pipeline via `tools/make_poster.py`
- Default quality target: P5.3/V6.2 adaptive mode. Use P5.3 when a real-person shop photo needs more polish while staying natural; use V6.2 when the priority is maximum documentary realism. Use P5.4 only when the output needs extra clarity for higher-resolution delivery.
- Fonts: `assets/fonts/NotoSansCJKsc-Regular.otf`, `assets/fonts/NotoSansCJKsc-Bold.otf`
- Output: `reports/*.jpg`

## Fast Command

```bash
tools/local_poster_generator.py \
  --image /path/to/photo.jpg \
  --style food \
  --layout photo-large \
  --topic "街坊热汤，现煮现做，温暖人情味" \
  --use-qwen
```

## Premium Command

```bash
tools/local_poster_premium.py \
  --image /path/to/photo.jpg \
  --enhance \
  --enhance-preset soft \
  --enhance-strength 0.45 \
  --style food \
  --layout natural-cover \
  --output reports/premium_food_poster.jpg
```

Premium mode uses local HTML/CSS layout and screenshots it with Playwright/Chromium.
It is better for Canva-like spacing, shadows, typography, and maintainable templates.
The preferred V6.2 mode for real people is `natural-cover`: natural documentary color, soft enhancement, clear typography, and restrained poster styling.
For person-first blessing posters, add `--auto-photo-position` so the renderer
uses face/subject analysis to pick a safer crop.

## P5 Photo Enhancement

Use P5 enhancement before premium rendering when source photos are compressed,
dim, flat, or low contrast.

```bash
tools/local_photo_enhance.py \
  --image /path/to/photo.jpg \
  --preset portrait \
  --strength 0.75 \
  --output reports/enhanced/photo_enhanced.jpg
```

Preset guidance:

- `soft --strength 0.45`: V6.2 default for real people and life scenes; keeps faces and color natural.
- `p53 --strength 0.48`: P5.3 default for real-person food stall photos; protects skin tone, suppresses over-strong reds, and keeps tile/wall regions neutral.
- `portrait --strength 0.75`: stronger real-person correction when the photo is dim or flat.
- `food --strength 1.0`: food/product/stall shots with no important face detail.
- `poster --strength 1.0`: general photos.
- `soft --strength 0.7`: fragile old photos or images that already look sharp but need mild correction.

## Styles

- `teacher`: 教师节 / 感恩 / 活动合照
- `food`: 街坊美食 / 热汤 / 手作温度
- `community`: 社区活动 / 温暖记录 / 通用宣传

## Layouts

- `photo-large`: large image, compact text panel
- `balanced`: image and text panel balanced, better for group photos with longer copy
- `story-cover`: V3 default quality mode, full-bleed cover poster with stronger visual impact
- `editorial-cover`: V4 experimental high-impact mode, magazine-ad style with full-screen photo, cinematic gradient, glass copy panel, and side label
- `natural-cover`: V6 natural documentary mode, preferred when real people and natural color matter more than cinematic impact
- `portrait-blessing`: full-photo person blessing poster with lower text panel; use with `--auto-photo-position`

## Telegram Routing Target

Recommended flow:

1. User sends image + short instruction.
2. Select style from intent:
   - 教师节 / 老师 / 感恩 -> `teacher`
   - 美食 / 汤 / 小贩 / 现煮 -> `food`
   - 活动 / 社区 / 关怀 -> `community`
3. Check GPU before `--use-qwen`.
4. Generate poster locally:
   - Fast default: `local_poster_generator.py`
   - P5.3 default for real-person shop/food-stall photos: `local_poster_premium.py --enhance --enhance-preset p53 --enhance-strength 0.48 --layout natural-cover`
   - P5.4 high-resolution option: `comfy_p54_upscale.py --image input.jpg --output reports/p54.png --max-edge 2600`, then `local_poster_premium.py --image reports/p54.png --layout natural-cover`
   - V6.2 maximum natural documentary mode: `local_poster_premium.py --enhance --enhance-preset soft --enhance-strength 0.45 --layout natural-cover`
   - V3 strong cover for product/food-only shots: `local_poster_premium.py --enhance --enhance-preset food --enhance-strength 0.8 --layout story-cover`
   - V4 high-impact experiment only when requested: `local_poster_premium.py --enhance --enhance-preset portrait --enhance-strength 0.6 --layout editorial-cover`
   - Person blessing poster: `local_poster_premium.py --layout portrait-blessing --auto-photo-position --enhance --enhance-preset soft --enhance-strength 0.42`
5. Send final JPG back with the `message` tool attachment.

## P5.10 Layout Guard

Use P5.10 when a photo contains people and text placement/crop safety matters:

```bash
tools/poster_layout_guard.py \
  --image /path/to/photo.jpg \
  --layout portrait-blessing \
  --output reports/layout_guard.json
```

It returns:

- face count and primary face box;
- subject center percentage;
- recommended CSS `background-position`;
- text-zone risk for lower-panel layouts.

Renderers can consume this automatically:

```bash
tools/local_poster_premium.py \
  --image /path/to/photo.jpg \
  --layout portrait-blessing \
  --auto-photo-position \
  --output reports/person_blessing.jpg
```

The quality gate can also check the original source photo:

```bash
tools/poster_quality_gate.py \
  --image reports/person_blessing.jpg \
  --source-image /path/to/photo.jpg \
  --layout portrait-blessing
```

This adds face count, subject center, and text-zone risk to the score output.

## P5.3 / V6.2 Routing Rule

Default decision:

- Real person visible in local shop/food-stall scene and poster needs polish -> `natural-cover`, `p53`, `0.48`.
- Real person visible and user wants clearer/high-resolution delivery -> P5.4 ComfyUI RealESRGAN upscale first, then `natural-cover` with no additional strong enhancement.
- Real person visible and user complains about unnatural color or asks for the most natural look -> `natural-cover`, `soft`, `0.45`.
- Food/product only and user wants advertising impact -> `story-cover`, `food`, `0.8`.
- User explicitly asks for cinematic, magazine, extreme, or test limit -> `editorial-cover`, conservative enhancement.
- If a generated image looks unnatural, reduce enhancement strength first before changing layout.

## P5.5 Quality Gate

Use P5.5 after rendering when multiple outputs look close or when checking for
common poster problems:

```bash
tools/poster_quality_gate.py \
  --image reports/premium_food_poster.jpg \
  --source-image /path/to/source.jpg \
  --layout natural-cover \
  --json-output reports/p55_quality.json \
  --md-output reports/p55_quality.md
```

The gate scores luma, contrast, saturation, sharpness, clipping, red dominance,
skin-tone stability, and optional layout safety when `--source-image` is given.
Treat the score as a routing signal, not a replacement for final visual review.

## P5.6 Version Matrix

Use P5.6 when Jason asks to compare versions or when the best mode is unclear:

```bash
tools/poster_version_matrix.py \
  --image /path/to/photo.jpg \
  --style food \
  --auto-photo-position
```

Default matrix:

- `p53`: `natural-cover + p53 0.48`
- `v62`: `natural-cover + soft 0.45`
- `v3`: `story-cover + food 0.8`

Outputs are archived under `reports/matrix/<run-id>/`:

- `p53.jpg`, `v62.jpg`, `v3.jpg`
- `scores.json`
- `report.md`
- `comparison.jpg`

Use `--include-p54` only when high-resolution clarity is required and ComfyUI is
already healthy, because it calls the local ComfyUI P5.4 upscale pipeline.

## P5.7 Auto Select

Use P5.7 when the workflow should generate, score, decide, and prepare the
Telegram send package:

```bash
tools/poster_auto_select.py \
  --image /path/to/photo.jpg \
  --style food \
  --auto-photo-position
```

P5.7 runs P5.6, reads `scores.json`, and writes:

- `send_manifest.json`
- `telegram_summary.md`
- `selected_best.jpg`
- `comparison.jpg`

Decision rule:

- If best score minus second score is at least `--score-gap` (default `2.0`), treat the top result as `auto_selected`.
- If the gap is below threshold, mark `needs_review` and send the comparison image so Jason can choose.

The script does not send Telegram messages directly. It leaves message delivery
to the agent-side `message` tool so chat credentials are not exposed to local
scripts.

## P5.8 Route Decision

Use P5.8 when only the image is known and the system should infer the poster
style and pipeline:

```bash
tools/poster_route_decision.py \
  --image /path/to/photo.jpg \
  --topic-hint "food stall poster"
```

P5.8 outputs `route_decision.json` with:

- `scene_type`
- `style`
- `primary_pipeline`
- `p54_recommended`
- `include_p54`
- image metrics such as skin percentage, warm food color percentage, red
  dominance, brightness, sharpness, and orientation
- the P5.7 command to run next

To run the full route-to-selection chain:

```bash
tools/poster_route_decision.py \
  --image /path/to/photo.jpg \
  --topic-hint "food stall poster" \
  --run-auto-select
```

P5.4 is recommendation-only by default. Add `--allow-p54` only when GPU/ComfyUI
use is explicitly desired:

```bash
tools/poster_route_decision.py \
  --image /path/to/photo.jpg \
  --allow-p54 \
  --run-auto-select
```

## P5.9 One-Command Entry

Use P5.9 as the default practical entrypoint when Jason says "做海报" or sends
an image with a short poster request:

```bash
tools/make_poster.py \
  --image /path/to/photo.jpg \
  --hint "food stall poster"
```

P5.9 wraps:

1. P5.8 route decision
2. P5.7 auto-select
3. Agent-facing `make_manifest.json`

Output directory:

`reports/make_poster/<run-id>/`

Key outputs:

- `make_manifest.json`: final agent-facing manifest
- `route_decision.json`: P5.8 route details
- `auto_select/send_manifest.json`: P5.7 selection details
- `auto_select/selected_best.jpg`
- `auto_select/comparison.jpg`

Agent send rule:

- If `make_manifest.json.decision == "auto_selected"`, send `selected_best.jpg`.
- If `decision == "needs_review"`, send `selected_best.jpg` and `comparison.jpg`.

P5.9 does not send Telegram messages directly. It prepares the manifest and
recommended attachments for the agent-side `message` tool.

## P5.11 — AI Copy Generation (local Qwen 3.5)

Generate poster copy based on scene type using local Ollama Qwen 3.5:

```bash
tools/local_ai_copy.py --scene food --language cn --hint "街坊汤店，热汤温暖人心"
tools/local_ai_copy.py --scene teacher --language en
```

Supported scenes: `food`, `teacher`, `community`, `youth`, `blessing`
Languages: `cn`, `en`, `bm`

Integrated into the premium renderer:

```bash
tools/local_poster_premium.py \
  --image /path/to/photo.jpg \
  --style food \
  --ai-copy --ai-copy-language cn \
  --ai-copy-hint "街坊汤店" \
  --enhance --enhance-preset p53
```

VRAM safety: checks `check_gpu.sh` before calling Ollama; falls back to
hardcoded defaults if VRAM exceeds 8000 MiB ceiling.

## P5.12 — Auto Color Palette Extraction

Extract dominant colors from the source photo and generate a matching palette:

```bash
tools/local_color_palette.py --image /path/to/photo.jpg --style food
```

Integrated into the premium renderer:

```bash
tools/local_poster_premium.py \
  --image /path/to/photo.jpg \
  --style food \
  --auto-color \
  --enhance --enhance-preset p53
```

The palette extracts 5 dominant colors via KMeans clustering, then generates:
- `accent_hex` / `accent2_hex`: poster accent and gradient colors
- `bg_hex` / `bg_dark_hex`: background tints
- `text_light_hex` / `text_dark_hex`: text-safe colors
- `dominant_colors_hex`: 5 dominant colors from the source photo

Palette type adapts based on style: warm tones for food/teacher/community;
cool/vibrant for youth.

## P5.13 — Multi-Language Poster Output

Generate CN/EN/BM versions of the same poster from one command:

```bash
tools/local_poster_i18n.py \
  --image /path/to/photo.jpg \
  --style food \
  --languages cn en bm \
  --enhance-preset p53 \
  --enhance-strength 0.48 \
  --ai-copy --auto-color
```

Outputs:
- `poster_cn.jpg`
- `poster_en.jpg`
- `poster_bm.jpg`
- `i18n_summary.md`

Use `--ai-copy` to get AI-generated copy per language; otherwise shares the
same hardcoded copy in all languages.

## P5.14 — Batch Processing

Process multiple images through the full P5.9 pipeline:

```bash
tools/local_poster_batch.py \
  --images photo1.jpg photo2.jpg photo3.jpg \
  --hint "food stall"
```

Or from a directory:

```bash
tools/local_poster_batch.py \
  --directory /path/to/photos/ \
  --hint "community event" \
  --max-images 20
```

Outputs:
- `batch_results.json`: full JSON with per-image manifests
- `batch_summary.md`: Markdown summary table
- `batch_index.html`: visual HTML gallery with previews
- Per-image subdirectories with full P5.9 outputs

## Runtime Dependencies

Playwright CLI is available through `npx playwright`.

Chromium runtime is installed under:

`/home/jason2ykk/.cache/ms-playwright/`

Because the WSL environment does not use sudo for system packages, required Chromium shared libraries are vendored under:

`vendor/playwright-libs/lib`

The premium renderer automatically prepends that directory to `LD_LIBRARY_PATH`.

## Safety

- No Canva API.
- No Photoshop API.
- No external image upload.
- Qwen is optional.
- Pillow rendering is fully local.
- Premium Playwright rendering is local after the Chromium runtime is installed.
