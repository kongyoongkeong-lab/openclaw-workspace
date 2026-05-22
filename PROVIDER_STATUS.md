# Provider Status — 2026-05-22

## Video

Configured:

- `google` — default `veo-3.1-fast-generate-preview`

Supported by current Google configuration:

- Text-to-video
- Image-to-video
- Video/reference-to-video where model supports it
- Durations: 4 / 6 / 8 seconds
- Aspect ratio / resolution / size parameters where supported

Listed but not configured at last check:

- `openai` / Sora
- `runway`
- `minimax`
- `fal`
- `qwen` / `alibaba` Wan
- `byteplus`
- `deepinfra`
- `together`
- `xai`
- `comfy`

## Rule

User-facing capability claims must say **configured** vs **available if API key is added**. Protocol templates under `workflows/video/` are repository assets, not proof of active provider availability.
