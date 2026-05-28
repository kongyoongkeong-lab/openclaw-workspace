#!/usr/bin/env python3
"""Local poster generator for OpenClaw Telegram image workflows.

Pipeline:
1. Optional local Qwen copy generation through Ollama.
2. Deterministic Pillow poster rendering.
3. JPG output under reports/ by default.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FONT_REG = ROOT / "assets/fonts/NotoSansCJKsc-Regular.otf"
FONT_BOLD = ROOT / "assets/fonts/NotoSansCJKsc-Bold.otf"


STYLE_PRESETS = {
    "teacher": {
        "title": "教师节快乐",
        "subtitle": "一份甜甜的心意，献给用心付出的老师们",
        "body": "今天的笑容很温暖，手中的蛋糕很甜。感谢每一位老师的耐心、关怀与坚持，因为有你们，孩子的成长路上多了一份光。",
        "badge": "感恩有您 · 一路同行",
        "footer": "温暖 · 感恩 · 值得",
        "palette": "gold",
    },
    "food": {
        "title": "一碗热汤的温度",
        "subtitle": "藏着最朴实的用心",
        "body": "热气升起，是熟悉的老味道；一勺一碗，都是认真生活的坚持。",
        "badge": "现煮现做 · 暖心好味道",
        "footer": "用心熬出日常里的小幸福",
        "palette": "orange",
    },
    "community": {
        "title": "温暖在身边",
        "subtitle": "每一份用心，都值得被看见",
        "body": "平凡的日常里，藏着最真诚的付出。一个笑容、一份心意，都让这个时刻更有温度。",
        "badge": "用心付出 · 温暖同行",
        "footer": "记录值得被记得的瞬间",
        "palette": "gold",
    },
}


def ensure_assets() -> None:
    missing = [str(p) for p in (FONT_REG, FONT_BOLD) if not p.exists()]
    if missing:
        raise SystemExit(
            "Missing required CJK font(s): "
            + ", ".join(missing)
            + "\nRun the previous font download step or place NotoSansCJKsc fonts in assets/fonts/."
        )


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def run_qwen(topic: str, style: str, image_hint: str = "") -> dict[str, str]:
    prompt = f"""
    你是中文海报文案助手。为一张手机竖版海报写简洁文案。
    主题：{topic}
    风格：{style}
    图片线索：{image_hint}

    只输出 JSON，不要解释。字段：
    title: 8字以内主标题
    subtitle: 18字以内副标题
    body: 45字以内正文
    badge: 12字以内按钮式短句
    footer: 14字以内底部短句
    """
    cmd = ["ollama", "run", "qwen3.5:9b", textwrap.dedent(prompt).strip()]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=45, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    text = proc.stdout.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    allowed = {"title", "subtitle", "body", "badge", "footer"}
    return {k: str(v).strip() for k, v in data.items() if k in allowed and str(v).strip()}


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        line = ""
        for ch in paragraph:
            test = line + ch
            if draw.textlength(test, font=fnt) <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = ch
        if line:
            lines.append(line)
    return lines


def centered(draw: ImageDraw.ImageDraw, canvas_w: int, y: int, text: str, fnt, fill) -> None:
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((canvas_w - (box[2] - box[0])) / 2, y), text, font=fnt, fill=fill)


def make_poster(image_path: Path, copy: dict[str, str], output: Path, layout: str) -> Path:
    width, height = 1080, 1620
    img = Image.open(image_path).convert("RGB")

    if layout == "photo-large":
        photo_h, panel_y, panel_h = 1020, 1135, 400
        photo_center = (0.52, 0.52)
    else:
        photo_h, panel_y, panel_h = 705, 830, 690
        photo_center = (0.5, 0.42)

    bg = ImageOps.fit(img, (width, height), method=Image.Resampling.LANCZOS, centering=photo_center)
    bg = ImageEnhance.Brightness(bg).enhance(0.74)
    bg = bg.filter(ImageFilter.GaussianBlur(24)).convert("RGBA")
    canvas = Image.alpha_composite(bg, Image.new("RGBA", (width, height), (255, 232, 196, 145)))
    draw = ImageDraw.Draw(canvas)

    for y in range(height):
        alpha = int(65 + 65 * (y / height))
        draw.line([(0, y), (width, y)], fill=(255, 228, 188, alpha))

    draw.ellipse((-170, -130, 270, 310), fill=(255, 204, 86, 70))
    draw.ellipse((850, 80, 1240, 470), fill=(255, 142, 104, 54))
    draw.ellipse((820, 1290, 1180, 1650), fill=(255, 202, 78, 52))

    photo_x, photo_y, photo_w = 70, 70, 940
    shadow = Image.new("RGBA", (photo_w + 36, photo_h + 36), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((18, 18, photo_w + 18, photo_h + 18), radius=44, fill=(35, 20, 10, 105))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)), (photo_x - 18, photo_y - 8))

    photo = ImageOps.fit(img, (photo_w, photo_h), method=Image.Resampling.LANCZOS, centering=photo_center)
    photo = ImageEnhance.Brightness(photo).enhance(1.05)
    photo = ImageEnhance.Contrast(photo).enhance(1.07).convert("RGBA")
    mask = Image.new("L", (photo_w, photo_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, photo_w, photo_h), radius=42, fill=255)
    canvas.paste(photo, (photo_x, photo_y), mask)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (photo_x, photo_y, photo_x + photo_w, photo_y + photo_h),
        radius=42,
        outline=(255, 248, 232, 235),
        width=8,
    )

    panel_x, panel_w = 70, 940
    draw.rounded_rectangle(
        (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
        radius=36,
        fill=(255, 249, 236, 242),
        outline=(225, 158, 78, 210),
        width=3,
    )

    title_f = font(74 if len(copy["title"]) > 5 else 86, True)
    subtitle_f = font(38, True)
    body_f = font(34 if layout == "photo-large" else 35)
    badge_f = font(30 if len(copy["badge"]) > 9 else 38, True)
    small_f = font(25)

    title_y = panel_y + (42 if layout == "photo-large" else 50)
    centered(draw, width, title_y, copy["title"], title_f, (126, 58, 25, 255))
    centered(draw, width, title_y + 88, copy["subtitle"], subtitle_f, (181, 91, 39, 255))
    draw.rounded_rectangle((280, title_y + 150, 800, title_y + 158), radius=4, fill=(224, 151, 72, 230))

    body_lines = wrap(draw, copy["body"], body_f, 800)
    y = title_y + 195
    for line in body_lines[:5]:
        box = draw.textbbox((0, 0), line, font=body_f)
        draw.text(((width - (box[2] - box[0])) / 2, y), line, font=body_f, fill=(78, 58, 44, 255))
        y += 50

    badge = copy["badge"]
    bw = int(draw.textlength(badge, font=badge_f)) + 80
    bx = (width - bw) // 2
    by = min(panel_y + panel_h - 76, y + 18)
    draw.rounded_rectangle((bx, by, bx + bw, by + 62), radius=31, fill=(194, 82, 33, 255))
    box = draw.textbbox((0, 0), badge, font=badge_f)
    draw.text(((width - (box[2] - box[0])) / 2, by + 8), badge, font=badge_f, fill=(255, 255, 246, 255))

    footer = copy["footer"]
    box = draw.textbbox((0, 0), footer, font=small_f)
    draw.text(((width - (box[2] - box[0])) / 2, 1565), footer, font=small_f, fill=(118, 82, 55, 230))

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=94, subsampling=1)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a local Chinese poster from an image.")
    parser.add_argument("--image", required=True, type=Path, help="Input image path")
    parser.add_argument("--topic", default="", help="Poster topic or instruction")
    parser.add_argument("--style", choices=sorted(STYLE_PRESETS), default="community")
    parser.add_argument("--layout", choices=["photo-large", "balanced"], default="photo-large")
    parser.add_argument("--use-qwen", action="store_true", help="Use local qwen3.5:9b through Ollama for copy")
    parser.add_argument("--title")
    parser.add_argument("--subtitle")
    parser.add_argument("--body")
    parser.add_argument("--badge")
    parser.add_argument("--footer")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    ensure_assets()
    copy = dict(STYLE_PRESETS[args.style])
    copy.pop("palette", None)
    if args.use_qwen:
        copy.update(run_qwen(args.topic or args.style, args.style))
    for key in ("title", "subtitle", "body", "badge", "footer"):
        value = getattr(args, key)
        if value:
            copy[key] = value

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = args.output or (REPORTS / f"local_poster_{args.style}_{timestamp}.jpg")
    result = make_poster(args.image, copy, output, args.layout)
    print(result)


if __name__ == "__main__":
    main()
