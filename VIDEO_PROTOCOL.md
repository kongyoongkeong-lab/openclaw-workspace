# 🎬 Video Generation Protocol — v1

**Engine:** ComfyUI v0.22.0 (CPU mode)
**Models:** Wan 2.2, LTX 2.0/2.3, CogVideo, HunyuanVideo
**API:** ComfyOrg API Key (remote GPU capable)
**Templates:** Git-tracked workflow JSONs
**Updated:** 2026-05-22

## Pipeline

```
User request ("generate a video of X")
  │
  ▼
┌──────────────────────────────────────┐
│ 1. SELECT MODEL                       │
│    - Wan 2.2: best quality, slowest   │
│    - LTX 2.3: faster, good quality    │
│    - HunyuanVideo: Chinese-friendly   │
│    - CogVideo: open-source            │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 2. SELECT MODE                       │
│    - Text-to-Video (txt2vid)         │
│    - Image-to-Video (img2vid)        │
│    - First-Last-Frame to Video       │
│    - Canny/Depth to Video            │
│    - Video Upscale                   │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 3. LOAD WORKFLOW TEMPLATE            │ ← GitHub-tracked
│    workflows/video/ directory        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 4. QUEUE TO COMIFYUI                 │ ← comfy_client.py
│    POST /prompt with workflow JSON   │
│    Include api_key_comfy_org         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 5. MONITOR + RETRIEVE                │
│    Poll queue/history for completion │
│    Download video output             │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ 6. DELIVER                           │ ← @comms
│    Attach video to message           │
│    Include generation params         │
└──────────────────────────────────────┘
```

## GitHub Integration

### Workflow Templates (git-tracked)

```
workflows/video/
├── README.md
├── txt2vid_wan2.2.json          # Text-to-Video (Wan 2.2)
├── txt2vid_ltx2.3.json          # Text-to-Video (LTX 2.3)
├── img2vid_wan2.2.json          # Image-to-Video (Wan 2.2)
├── img2vid_ltx2.3.json          # Image-to-Video (LTX 2.3)
├── first_last_to_vid.json       # First-Last-Frame interpolation
├── canny_to_vid_ltx2.0.json     # Canny edge → video
├── depth_to_vid_ltx2.0.json     # Depth map → video
├── video_upscale_gan.json       # GAN upscale x4
└── prompt_enhance.json          # Prompt enhancement node
```

### Prompt Library (git-tracked)

```
prompts/video/
├── README.md
├── styles/
│   ├── cinematic.md             # Cinematic video style
│   ├── anime.md                 # Anime video style
│   └── realistic.md             # Realistic video style
└── motion/
    ├── slow_camera_pan.md       # Slow pan
    ├── fast_action.md           # Fast action
    └── steady_static.md         # Static shot
```

## Available Models

> **⚠️ CPU Warning:** On CPU, video generation is extremely slow.
> Use the ComfyOrg API key to queue on remote GPU servers for video.

| Model | Mode | Quality | Speed | Blueprint |
|-------|------|---------|-------|-----------|
| **Wan 2.2** | txt2vid / img2vid | ⭐⭐⭐ Best | Slow | ✅ Built-in |
| **LTX 2.3** | txt2vid / img2vid | ⭐⭐ Good | Fast | ✅ Built-in |
| **LTX 2.0** | Canny/Depth/First-Last | ⭐⭐ Good | Fast | ✅ Built-in |
| **HunyuanVideo** | txt2vid / img2vid | ⭐⭐⭐ Best | Slow | Built-in nodes |
| **CogVideo** | txt2vid | ⭐⭐ Good | Medium | Built-in nodes |

## Remote GPU Workflow (Recommended)

Since local CPU inference is slow, video generation is best done via the ComfyOrg API:

```python
import json
from urllib import request

workflow = json.load(open("workflows/video/txt2vid_wan2.2.json"))
payload = {
    "prompt": workflow,
    "extra_data": {
        "api_key_comfy_org": os.environ["COMFY_API_KEY"]
    }
}
req = request.Request("http://127.0.0.1:8188/prompt",
    data=json.dumps(payload).encode("utf-8"))
resp = request.urlopen(req)
```

## CLI Usage

```bash
# List available video workflows
cd ~/openclaw-stack/comfyui-native
python3 -c "import comfy_client; comfy_client.list_workflows()"

# Queue a video workflow
python3 comfy_client.py ~/.openclaw/workspace/workflows/video/txt2vid_wan2.2.json

# Queue with prompt override
COMFY_API_KEY="$COMFY_API_KEY" python3 -c "
import comfy_client as cc
result = cc.queue_with_prompt(
    '$HOME/.openclaw/workspace/workflows/video/txt2vid_wan2.2.json',
    prompt_text='a serene river flowing through a forest, cinematic lighting',
    prompt_node_id='6'
)
print(result)
"
```

## Video Prompt Engineering

### Structure
```
[Subject], [action/motion], [environment], [camera movement],
[lighting], [style], [duration hint], [quality tags]
```

### Motion Keywords
```
slow motion, time lapse, cinematic camera pan, tracking shot
dolly zoom, aerial drone shot, handheld, steady cam
fast action, explosion, speed ramp, slow reveal
```

### Example Prompts

**Cinematic:** "A majestic eagle soaring over mountain peaks, cinematic camera pan following its flight, golden hour lighting, 8k, masterpiece"

**Anime:** "Anime girl walking through a cherry blossom street, slow motion petals falling, soft pastel colors, steady cam"

**Product:** "A luxury watch rotating on a turntable, studio lighting, macro lens, smooth 360 rotation, photorealistic, 4k"

## Node Config Reference

| Parameter | Wan 2.2 | LTX 2.3 | Hunyuan |
|-----------|---------|---------|---------|
| Max frames | 81-161 | 97-193 | 129 |
| Recommended steps | 30-50 | 20-30 | 30-50 |
| CFG scale | 5.0-7.0 | 3.0-5.0 | 6.0 |
| Resolution | 480p-720p | 512x512+ | 720p |

## Storage

| Data | GitHub? | Location |
|------|---------|----------|
| Workflow templates | ✅ Yes | `workflows/video/` |
| Prompt library | ✅ Yes | `prompts/video/` |
| Generated videos | ❌ No | `comfyui-native/output/` (temporary) |
| Model weights | ❌ No | Too large for git |
