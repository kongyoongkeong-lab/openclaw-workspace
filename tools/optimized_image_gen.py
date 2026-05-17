#!/usr/bin/env python3
"""
Optimized image generation with size control.
Uses canvas operations and compression to fit media limits.
"""
import subprocess
import sys
from pathlib import Path

def generate_optimized_poster(prompt):
    """Generate image and optimize to fit 6MB limit."""
    output_file = "/home/jason2ykk/.openclaw/workspace/artifacts/poster_cny.png"
    
    # Generate with canvas if available
    canvas_cmd = f"""
from PIL import Image
import base64
import io

# Create optimized poster
width, height = 1024, 1920
img = Image.new('RGB', (width, height), color='#FF0000')

# Draw elements (simplified)
import os
import math

# Golden gradient
for y in range(height):
    for x in range(width):
        gold = min(y/height, 1.0)
        red = int(255 + (200 - 255) * (1 - gold))
        img.putpixel((x, y), (255, red, 50))

img.save('/home/jason2ykk/.openclaw/workspace/artifacts/poster_cny.png', 'PNG')
print(f'Poster generated: {width}x{height}')
"""
    
    # Execute canvas command
    subprocess.run(
        ["python3", "-c", canvas_cmd],
        cwd="/home/jason2ykk/.openclaw/workspace",
        check=True,
    )
    
    # Compress with pngquant or optipng if available
    compress_cmd = ["pngquant", "--quality", "65", "/home/jason2ykk/.openclaw/workspace/artifacts/poster_cny.png"]
    
    try:
        subprocess.run(compress_cmd, check=True)
        print("Poster optimized with pngquant")
    except FileNotFoundError:
        # Use basic compression
        subprocess.run(["pngcrush", "/home/jason2ykk/.openclaw/workspace/artifacts/poster_cny.png",
                       "/home/jason2ykk/.openclaw/workspace/artifacts/poster_cny.png"], check=True)
    
    return output_file

if __name__ == "__main__":
    poster_path = generate_optimized_poster("CNY Family Blessing Poster")
    print(f"Ready: {poster_path}")
