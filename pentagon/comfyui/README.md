# Pentagon ComfyUI Production Stack

## 📋 Quick Start

### Manual UI (for validation)
```bash
open http://localhost:8188
Workflow → Load Default
Select: sd_xl_base_1.0.safetensors
Queue Prompt
```

### API Automation (Production)
```bash
./queue_generation.sh workflows/first_sdxl_workflow.json
./check_queue.sh
```

### Python Bridge
```bash
python3 comfyui_bridge.py
```

## 📁 Directory Structure

```
~/pentagon/comfyui/
├── workflows/          # Saved node graphs (.json)
├── templates/          # Template workflows
├── input/              # ControlNet inputs
├── output/             # Generated PNGs
├── upscale/            # Upscaled outputs
├── api/                # API scripts
└── automation/         # Automation scripts
```

## 🎯 Next Steps

1. **First Generation:** Use UI to generate first image
2. **Save Workflow:** `Workflow → Save` as JSON
3. **Test API:** `./queue_generation.sh [workflow.json]`
4. **OpenClaw Bridge:** Integrate via `@ops generate poster`

## 📊 GPU Limits

- VRAM: 8.5GB (safe ceiling)
- Utilization: 70-95%
- OOM: Auto-restart
