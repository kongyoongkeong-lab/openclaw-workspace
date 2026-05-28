#!/usr/bin/env python3
"""P5.11 AI copy generation for local posters.

Calls local Ollama Qwen to generate poster copy (title, subtitle, body, badge,
footer) based on scene type and optional user hint. All inference is local;
nothing is sent to any external API.

VRAM check: calls check_gpu.sh before running to confirm GPU is safe.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECK_GPU = ROOT / "tools/check_gpu.sh"
VRAM_HARD_CEILING = 8000  # MiB — leave headroom below 9728 for safety


@dataclass
class AICopyResult:
    scene_type: str
    language: str
    title: str
    subtitle: str
    body: str
    badge: str
    footer: str
    raw_output: str
    vram_mib: int
    warnings: list[str]


SCENE_PROMPTS: dict[str, str] = {
    "teacher": (
        "你是一个海报文案策划。请为一张教师节/感恩主题的海报生成以下5段文案。"
        "风格要求：温暖、真诚、有画面感，20-30岁教师受众。\n"
        "返回格式：\n"
        "【标题】\n"
        "【副标题】\n"
        "【正文】\n"
        "【标签】\n"
        "【脚注】\n"
    ),
    "food": (
        "你是一个海报文案策划。请为一张街坊美食/小店海报生成以下5段文案。"
        "风格要求：有烟火气、接地气、温暖，像古早味小店会贴的那种。\n"
        "返回格式：\n"
        "【标题】\n"
        "【副标题】\n"
        "【正文】\n"
        "【标签】\n"
        "【脚注】\n"
    ),
    "community": (
        "你是一个海报文案策划。请为一张社区活动/人物关怀/温暖记录的海报生成以下5段文案。"
        "风格要求：真实、温暖、有生活感，不要广告腔。\n"
        "返回格式：\n"
        "【标题】\n"
        "【副标题】\n"
        "【正文】\n"
        "【标签】\n"
        "【脚注】\n"
    ),
    "youth": (
        "你是一个海报文案策划。请为一张展示年轻人青春活力和希望的海报生成以下5段文案。"
        "风格要求：青春、热血、充满希望，用简短有力的祝福语。\n"
        "返回格式：\n"
        "【标题】\n"
        "【副标题】\n"
        "【正文】\n"
        "【标签】\n"
        "【脚注】\n"
    ),
    "blessing": (
        "你是一个海报文案策划。请为一张祝福/关怀主题的海报生成以下5段文案。"
        "风格要求：温暖、平安、幸福、有生活气息，适合送给长辈或亲友。\n"
        "返回格式：\n"
        "【标题】\n"
        "【副标题】\n"
        "【正文】\n"
        "【标签】\n"
        "【脚注】\n"
    ),
}


def check_vram() -> int:
    """Return current used VRAM in MiB. Returns 0 if check_gpu.sh not found."""
    if not CHECK_GPU.exists():
        return 0
    proc = subprocess.run(
        ["bash", str(CHECK_GPU)],
        text=True, capture_output=True, check=False, timeout=30,
    )
    for line in (proc.stdout + proc.stderr).splitlines():
        m = re.search(r"Used\s*:\s*(\d+)\s*MiB", line, re.IGNORECASE)
        if m:
            return int(m.group(1))
    for line in (proc.stdout + proc.stderr).splitlines():
        m = re.search(r"(\d+)\s*/\s*\d+\s*MiB", line)
        if m:
            return int(m.group(1))
    return 0


def run_ollama(prompt: str, timeout: int = 60) -> str:
    """Call local qwen3.5:9b via Ollama. Returns raw stdout."""
    cmd = ["ollama", "run", "qwen3.5:9b", prompt]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=timeout)
    if proc.returncode != 0:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        raise RuntimeError(f"Ollama call failed:\n{combined}")
    return proc.stdout.strip()


_SECTION_PATTERN = re.compile(
    r"【(标题|副标题|正文|标签|脚注)】\s*(.*?)(?=\n【|\Z)", re.DOTALL
)


def parse_sections(raw: str) -> dict[str, str]:
    """Parse the 5-section output from Ollama."""
    sections = {}
    for full_match in _SECTION_PATTERN.finditer(raw):
        key = full_match.group(1)
        value = full_match.group(2).strip().replace("\n", " ").strip()
        sections[key] = value

    # Fallback: try line-based parsing
    if not sections:
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        for line in lines:
            for key in ("标题", "副标题", "正文", "标签", "脚注"):
                if line.startswith(key) or line.startswith(f"【{key}】"):
                    value = line.split("】", 1)[-1] if "】" in line else line.split(key, 1)[-1]
                    value = value.strip("：: ").strip()
                    if key not in sections:
                        sections[key] = value
    return sections


def generate(
    scene_type: str,
    language: str = "cn",
    hint: str = "",
    timeout: int = 60,
    skip_vram_check: bool = False,
) -> AICopyResult:
    """Generate AI copy. Returns AICopyResult with defaults if Ollama unavailable."""
    warnings: list[str] = []
    vram_mib = 0

    if not skip_vram_check:
        vram_mib = check_vram()
        if vram_mib > VRAM_HARD_CEILING:
            warnings.append(f"VRAM {vram_mib}MiB exceeds ceiling {VRAM_HARD_CEILING}MiB; skipping AI copy")
            return _fallback(scene_type, language, "", warnings, vram_mib)

    prompt = SCENE_PROMPTS.get(scene_type, SCENE_PROMPTS["community"])
    if language == "en":
        prompt = prompt.replace("中文", "英文").replace("请为", "Please write English copy for")
    elif language == "bm":
        prompt = prompt.replace("中文", "Bahasa Melayu").replace("请为", "Sila tulis salinan Bahasa Melayu untuk")
    if hint:
        prompt += f"\n额外要求：{hint}"

    raw_output = run_ollama(prompt, timeout=timeout)
    parsed = parse_sections(raw_output)

    result = {
        "scene_type": scene_type,
        "language": language,
        "title": parsed.get("标题", ""),
        "subtitle": parsed.get("副标题", ""),
        "body": parsed.get("正文", ""),
        "badge": parsed.get("标签", ""),
        "footer": parsed.get("脚注", ""),
        "raw_output": raw_output,
        "vram_mib": vram_mib,
        "warnings": warnings,
    }

    # If any section is empty, fill from fallback
    fallback = _fallback(scene_type, language, "", [], vram_mib)
    for key in ("title", "subtitle", "body", "badge", "footer"):
        if not result[key]:
            result[key] = getattr(fallback, key)
            if not any("AI copy incomplete" in w for w in result["warnings"]):
                result["warnings"].append("AI copy incomplete; fallback used for some fields")

    return AICopyResult(**result)


def _fallback(
    scene_type: str, language: str, hint: str, warnings: list[str], vram_mib: int
) -> AICopyResult:
    """Return hardcoded defaults when AI is unavailable."""
    if language == "en":
        fallbacks: dict[str, dict[str, str]] = {
            "food": {
                "title": "A Bowl of Warmth",
                "subtitle": "Simple Ingredients, Sincere Heart",
                "body": "Steam rises with a familiar old taste. Every spoonful is a quiet dedication to everyday life.",
                "badge": "Freshly Cooked · Warmth in Every Bowl",
                "footer": "The little happiness found in everyday flavours",
            },
            "teacher": {
                "title": "Happy Teachers' Day",
                "subtitle": "A Sweet Thank-You for Every Patient Heart",
                "body": "Your smile is the best gift. Every effort is worth it because you light the way.",
                "badge": "Grateful · Together We Grow",
                "footer": "Warmth · Gratitude · Worth It",
            },
            "youth": {
                "title": "Youth · Hope · Light",
                "subtitle": "May you shine with dreams in your eyes",
                "body": "Every step forward is a promise. You are young, you are bright, and your story has just begun.",
                "badge": "Dream Big · Shine Bright",
                "footer": "The future belongs to those who believe",
            },
            "blessing": {
                "title": "Peace · Joy · Love",
                "subtitle": "Wishing you happiness today and every day",
                "body": "May your heart be light, your home warm, and your days filled with quiet joy.",
                "badge": "Blessings & Warmth",
                "footer": "With love, today and always",
            },
        }
    elif language == "bm":
        fallbacks = {
            "food": {
                "title": "Secawan Kehangatan",
                "subtitle": "Resipi Lama, Hati yang Tulus",
                "body": "Wangian lama yang familiar. Setiap suapan adalah dedikasi pada kehidupan seharian.",
                "badge": "Masak Segar · Kehangatan Dalam Setiap Saji",
                "footer": "Kebahagiaan kecil dalam rasa seharian",
            },
            "teacher": {
                "title": "Selamat Hari Guru",
                "subtitle": "Terima Kasih untuk Setiap Kesabaran dan Kasih",
                "body": "Senyuman anda adalah hadiah terbaik. Setiap usaha adalah berbaloi.",
                "badge": "Bersyukur · Bersama Kita Maju",
                "footer": "Kehangatan · Syukur · Berbaloi",
            },
            "youth": {
                "title": "Muda · Harapan · Cahaya",
                "subtitle": "Semoga kau bersinar dengan impian di matamu",
                "body": "Setiap langkah adalah janji. Masa depan milik mereka yang percaya.",
                "badge": "Impian Besar · Bersinar Terang",
                "footer": "Masa depan milik mereka yang percaya",
            },
            "blessing": {
                "title": "Damai · Sukacita · Kasih",
                "subtitle": "Semoga hari-harimu dipenuhi kebahagiaan",
                "body": "Semoga hatimu ringan, rumahmu hangat, dan harimu penuh sukacita.",
                "badge": "Berkat & Kehangatan",
                "footer": "Dengan kasih, hari ini dan selamanya",
            },
        }
    else:
        fallbacks = {
            "food": {
                "title": "一碗热汤的温度",
                "subtitle": "最朴实的食材，最用心的坚持",
                "body": "热气升起，是熟悉的老味道；一勺一碗，都是认真生活的坚持。",
                "badge": "现煮现做·暖心好味道",
                "footer": "用心熬出日常里的小幸福",
            },
            "teacher": {
                "title": "教师节快乐",
                "subtitle": "一份甜甜的心意，献给用心付出的老师们",
                "body": "今天的笑容很温暖，手中的蛋糕很甜。感谢每一位老师的耐心、关怀与坚持。",
                "badge": "感恩有您·一路同行",
                "footer": "温暖·感恩·值得",
            },
            "youth": {
                "title": "青春正当时",
                "subtitle": "愿你眼里有光，心中有梦",
                "body": "每一步向前，都是对未来的承诺。年轻，就是最大的底气。",
                "badge": "勇敢追梦·不负韶华",
                "footer": "未来属于相信的人",
            },
            "blessing": {
                "title": "幸福·快乐·安康",
                "subtitle": "愿你每一天都被温柔以待",
                "body": "愿你的心温暖而轻盈，家中常伴笑声，日子过得安稳而明亮。",
                "badge": "温馨祝福·与你同行",
                "footer": "平安喜乐，岁岁年年",
            },
        }

    fb = fallbacks.get(scene_type, fallbacks["food"])
    return AICopyResult(
        scene_type=scene_type,
        language=language,
        title=fb["title"],
        subtitle=fb["subtitle"],
        body=fb["body"],
        badge=fb["badge"],
        footer=fb["footer"],
        raw_output="(fallback — no AI call)",
        vram_mib=vram_mib,
        warnings=warnings,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="P5.11 AI copy generation for local posters.")
    parser.add_argument("--scene", choices=sorted(SCENE_PROMPTS), default="food")
    parser.add_argument("--language", choices=["cn", "en", "bm"], default="cn")
    parser.add_argument("--hint", default="")
    parser.add_argument("--skip-vram-check", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout.")
    args = parser.parse_args()

    result = generate(
        scene_type=args.scene,
        language=args.language,
        hint=args.hint,
        timeout=args.timeout,
        skip_vram_check=args.skip_vram_check,
    )

    if args.json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(f"scene={result.scene_type} lang={result.language}")
        print(f"  title:    {result.title}")
        print(f"  subtitle: {result.subtitle}")
        print(f"  body:     {result.body}")
        print(f"  badge:    {result.badge}")
        print(f"  footer:   {result.footer}")
        if result.warnings:
            print(f"  warnings: {result.warnings}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
