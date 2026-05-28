# Local ComfyUI Photo Pipeline

Purpose: use the local ComfyUI container as an optional image-level enhancement
stage before the deterministic HTML/CSS poster renderer.

## Current Runtime

- ComfyUI URL: `http://127.0.0.1:8188`
- Container: `pentagon-comfyui`
- Version observed after restart: `0.20.1`
- GPU: RTX 4070 SUPER
- Active checkpoint: `sd_xl_base_1.0.safetensors`
- Custom upscale node: `ComfyUI_UltimateSDUpscale`
- Upscale model: `RealESRGAN_x4plus.pth`

## Tool

```bash
tools/comfy_photo_enhance.py \
  --image /path/to/photo.jpg \
  --output reports/comfy_photo.png \
  --denoise 0.16 \
  --steps 8 \
  --cfg 3.0
```

The script uses the ComfyUI HTTP API:

1. Upload input image with `/upload/image`.
2. Queue an SDXL img2img workflow with `/prompt`.
3. Poll `/history/{prompt_id}`.
4. Download the output through `/view`.

## P5.4 Upscale Tool

Use this when the same real-person poster needs a clearer source image for
higher-resolution delivery while avoiding an SDXL face redraw.

```bash
tools/comfy_p54_upscale.py \
  --image /path/to/photo.jpg \
  --output reports/comfy_p54_upscaled.png \
  --max-edge 2600
```

This uses `UpscaleModelLoader` + `ImageUpscaleWithModel` with
`RealESRGAN_x4plus.pth`, then constrains the downloaded image to a practical
maximum edge. It is safer for identity preservation than tiled diffusion redraw.

## Recommended Parameters

- Real-person shop/stall photos: `denoise 0.12-0.16`, `steps 8`, `cfg 3.0`.
- Product/food-only photos: `denoise 0.18-0.28`, `steps 10-14`, `cfg 3.5-4.5`.
- Avoid `denoise > 0.2` for visible faces unless the user explicitly wants AI restyling.

## Poster Integration

For real-person photos:

1. Run ComfyUI low-denoise enhancement.
2. Inspect face/identity preservation.
3. Send Comfy output directly into `tools/local_poster_premium.py`.
4. Do not stack strong P5.3 enhancement afterward unless the Comfy output is still flat.

Example:

```bash
tools/local_poster_premium.py \
  --image reports/comfy_photo.png \
  --style food \
  --layout natural-cover \
  --output reports/premium_food_poster_comfy.jpg
```

## Current Limitation

After restart, `/workspace` is mounted from
`/home/jason2ykk/pentagon/comfyui/comfyui` and persists correctly. Use the HTTP
API for image input/output by default; write model and custom-node files into
the bind mount only when installing/upgrading ComfyUI assets.

## Safety

- Check VRAM before running local diffusion.
- Keep used VRAM below `9728 MiB`.
- Prefer low-denoise img2img for real people.
- Treat ComfyUI as optional; P5.3 local OpenCV/Pillow remains the default for
  natural documentary photos.
- Treat P5.4 as a clarity/upscale layer, not the default look. It can sharpen
  faces slightly, so compare against P5.3 before using it as final output.
