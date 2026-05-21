# 🎨 Image Generation Protocol — v1

**Engine:** ComfyUI (CPU mode)
**API:** ComfyOrg API Key (remote GPU capable)
**Storage:** Local + GitHub templates
**Updated:** 2026-05-22

## Pipeline

```
User request ("generate an image of X")
  │
  ▼
┌──────────────────────────────────────┐
│ 1. PROMPT ENGINEERING                │ ← @main crafts the prompt
│    - Style: realistic/anime/3D/photo │
│    - Dimensions: 512x512, 1024x1024  │
│    - Negative prompt (if needed)     │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 2. WORKFLOW SELECTION                │ ← GitHub-tracked templates
│    - Check workflows/ directory      │
│    - Match workflow to request type  │
│    - Fallback: default txt2img       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 3. API QUEUE                         │ ← comfy_client.py
│    - POST /prompt with workflow JSON │
│    - Attach api_key_comfy_org        │
│    - Return prompt_id                │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 4. MONITOR + RETRIEVE                │ ← Poll queue/history
│    - GET /history/{prompt_id}        │
│    - Download output images          │
│    - Save to output/ directory       │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 5. DELIVER                           │ ← @comms
│    - Attach image to message         │
│    - Include generation params       │
│    - Optionally commit workflow      │
└──────────────────────────────────────┘
```

## GitHub Integration

### Workflow Templates (version controlled)

Workflow JSON files stored in `~/.openclaw/workspace/workflows/` → git-tracked:

```
workflows/
├── README.md
├── default_txt2img.json       # Basic text-to-image
├── default_img2img.json       # Basic image-to-image
├── upscale_4x.json            # Upscaling workflow
├── inpainting.json            # Inpaint/outpaint
├── realistic_portrait.json    # Portrait-specific settings
└── experimental/              # WIP workflows (git ignored?)
```

### Prompt Library (version controlled)

`prompts/` directory in workspace → git-tracked:

```
prompts/
├── README.md
├── styles/
│   ├── anime.md
│   ├── realistic.md
│   ├── cinematic.md
│   └── pixel_art.md
├── templates/
│   ├── portrait.md
│   ├── landscape.md
│   └── product_photo.md
└── negative_prompts.md
```

### What Gets Committed vs What Doesn't

| Data | GitHub? | Reason |
|------|---------|--------|
| Workflow JSON templates | ✅ Yes | Reusable, versioned |
| Prompt library (markdown) | ✅ Yes | Reusable, versioned |
| comfy_client.py | ✅ Yes | Core tool, versioned |
| API key | ❌ No | `~/.openclaw/credentials/` (secure) |
| Generated images | ❌ No | Too large, ephemeral |
| ComfyUI model files | ❌ No | Too large (GB+) |
| ComfyUI source code | ❌ No | External dependency |

## API Client Usage

```bash
cd ~/openclaw-stack/comfyui-native

# Queue a workflow from a template
python3 comfy_client.py ~/.openclaw/workspace/workflows/default_txt2img.json

# Queue with inline prompt override
python3 comfy_client.py queue \
  --workflow workflows/default_txt2img.json \
  --prompt "a cat wearing a spacesuit"

# Check queue status
python3 comfy_client.py --stats

# Get history/result
python3 comfy_client.py --history <prompt_id>

# List available models
python3 comfy_client.py --models
```

## Workflow Template Format

```json
{
  "workflow_name": "default_txt2img",
  "version": "1.0",
  "description": "Basic text-to-image generation",
  "prompt_override_node": "6",       // CLIPTextEncode node ID
  "default_params": {
    "steps": 20,
    "cfg": 7.0,
    "seed": -1,
    "width": 512,
    "height": 512
  },
  "comfy_workflow": { /* full ComfyUI API workflow JSON */ }
}
```

## ComfyOrg API Key (Remote GPU)

When pushing to a remote ComfyOrg endpoint instead of local:

```python
extra_data = {
    "api_key_comfy_org": os.environ["COMFY_API_KEY"]
}
```

The API key enables:
- Running workflows on remote GPU servers
- Accessing premium/specialized nodes (Gemini, ByteDance, etc.)
- Skipping authentication on the frontend

## Prompt Engineering Guidelines

### Structure
```
[Subject], [details], [style], [lighting], [composition], [quality_tags]
```

### Quality Tags
```
masterpiece, best quality, highly detailed, 8k, photorealistic
```

### Negative Prompts (common)
```
bad hands, missing fingers, extra limbs, blurry, low quality, watermark, text
```

### Example
```
"a serene Japanese garden with cherry blossoms, soft morning light,
 cinematic composition, masterpiece, best quality, highly detailed,
 8k, photorealistic"
```
