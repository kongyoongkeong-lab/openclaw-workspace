# ComfyUI Workflow Templates

在 GitHub 上通过版本控制管理可复用的 ComfyUI 工作流。

## 使用方法
```bash
python3 ~/openclaw-stack/comfyui-native/comfy_client.py workflows/default_txt2img.json
```

## Templates
| File | Type | Nodes |
|------|------|-------|
| `default_txt2img.json` | Text-to-image | KSampler + CLIP + VAE |
| `default_img2img.json` | Image-to-image | (coming soon) |
| `upscale_4x.json` | Upscaling | (coming soon) |

## Exporting
1. Build workflow in ComfyUI UI
2. File → Export (API format)
3. Save to this directory
4. Commit to GitHub
