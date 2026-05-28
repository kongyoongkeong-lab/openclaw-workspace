#!/usr/bin/env python3
"""Create Suno-ready song packs without account cookies or unofficial proxies."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_NEGATIVE = (
    "muddy mix, harsh sibilance, clipping, distorted vocals, off-key singing, "
    "unwanted rap, long intro, abrupt ending, crowd noise, low fidelity"
)

LANG_HINTS = {
    "english": {
        "hook": "still chasing light through the city rain",
        "promise": "we rise again before the night is done",
    },
    "chinese": {
        "hook": "我把光藏进夜色里",
        "promise": "天亮之前我们继续前行",
    },
    "bilingual": {
        "hook": "我把光藏进夜色里, still chasing light",
        "promise": "天亮之前, we rise again",
    },
}


@dataclass(frozen=True)
class Variant:
    name: str
    style: str
    prompt: str


@dataclass(frozen=True)
class SongPack:
    title: str
    theme: str
    genre: str
    mood: str
    language: str
    vocal: str
    use_case: str
    suno_style: str
    suno_prompt: str
    negative_tags: str
    lyrics: str
    variants: list[Variant]
    workflow: list[str]


def title_case_slug(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text)
    if not words:
        return "Untitled Track"
    if any(re.search(r"[\u4e00-\u9fff]", word) for word in words):
        return "".join(words[:8])
    return " ".join(word.capitalize() for word in words[:8])


def language_key(language: str) -> str:
    normalized = language.strip().lower()
    if normalized in {"cn", "zh", "chinese", "mandarin", "中文", "华语"}:
        return "chinese"
    if normalized in {"bilingual", "mixed", "中英", "双语"}:
        return "bilingual"
    return "english"


def build_lyrics(title: str, theme: str, language: str, mood: str) -> str:
    hints = LANG_HINTS[language_key(language)]
    if language_key(language) == "chinese":
        return f"""[Verse 1]
凌晨的街灯还没睡
风把回忆吹成灰
我听见心跳在倒退
却还想靠近一回

[Pre-Chorus]
如果遗憾也会发光
就让它照亮远方

[Chorus]
{hints["hook"]}
把你的名字轻轻拾起
{hints["promise"]}
就算世界安静得只剩呼吸

[Verse 2]
那些没说完的愿望
还在时间里回响
我沿着人海的方向
寻找没熄灭的光

[Bridge]
别怕风太冷
别怕梦太深
我们把破碎的片刻
唱成新的可能

[Final Chorus]
{hints["hook"]}
把所有沉默变成旋律
{hints["promise"]}
让这首歌替我们证明"""

    if language_key(language) == "bilingual":
        return f"""[Verse 1]
City lights are fading slow
我还在雨里等候
Every memory starts to glow
像没说出口的温柔

[Pre-Chorus]
If the night is all we know
就让心跳带路走

[Chorus]
{hints["hook"]}
Through the static, through the rain
{hints["promise"]}
We turn the heartbreak into flame

[Verse 2]
我把遗憾写成歌
You hear the echo in my soul
走过拥挤的银河
Still searching for a place called home

[Bridge]
Hold on, 别回头
Let go, 再自由
Every scar becomes a note
Every fall becomes a road

[Final Chorus]
{hints["hook"]}
Through the silence, through the pain
{hints["promise"]}
We turn tomorrow into flame"""

    return f"""[Verse 1]
Neon on the window, rain across the floor
I keep hearing echoes I cannot ignore
Every little heartbeat points me back to you
Like a faded signal breaking through the blue

[Pre-Chorus]
If the dark is all we have tonight
I will turn it into firelight

[Chorus]
{hints["hook"]}
Holding on to every word we never said
{hints["promise"]}
We will make a sunrise out of what we lost

[Verse 2]
Footsteps in the distance, headlights on the glass
I can feel the future pulling from the past
Nothing here is perfect, nothing here is clean
But I found a rhythm in the in-between

[Bridge]
Let the silence break
Let the skyline shake
Every scar can sing
When the morning wakes

[Final Chorus]
{hints["hook"]}
Holding on to every word we never said
{hints["promise"]}
We will make a sunrise out of what we lost"""


def build_pack(args: argparse.Namespace) -> SongPack:
    title = args.title or title_case_slug(args.theme)
    article = "an" if args.mood[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
    style_base = (
        f"{args.genre}, {args.mood}, {args.vocal} vocal, polished modern production, "
        f"radio-ready arrangement, strong chorus, clean master"
    )
    prompt = (
        f"Create a {args.language} song about {args.theme}. "
        f"Use {article} {args.mood} emotional arc for {args.use_case}. "
        "Structure: verse, pre-chorus, chorus, verse, bridge, final chorus. "
        "Keep the hook memorable and avoid overly long instrumental intros."
    )
    variants = [
        Variant(
            "main",
            style_base,
            prompt,
        ),
        Variant(
            "short-form hook",
            f"{args.genre}, punchy drums, immediate chorus, {args.mood}, social media hook",
            f"{prompt} Prioritize a hook within the first 10 seconds for TikTok/Reels.",
        ),
        Variant(
            "cinematic",
            f"cinematic {args.genre}, wide atmosphere, emotional build, {args.vocal} vocal",
            f"{prompt} Make it more dramatic, spacious, and soundtrack-like.",
        ),
    ]
    return SongPack(
        title=title,
        theme=args.theme,
        genre=args.genre,
        mood=args.mood,
        language=args.language,
        vocal=args.vocal,
        use_case=args.use_case,
        suno_style=style_base,
        suno_prompt=prompt,
        negative_tags=args.negative,
        lyrics=args.lyrics or build_lyrics(title, args.theme, args.language, args.mood),
        variants=variants,
        workflow=[
            "Open Suno Pro and choose Custom mode.",
            "Paste the lyrics into Lyrics.",
            "Paste the selected style into Style of Music.",
            "Use the title as the song title.",
            "Generate 2-4 candidates, then keep notes on clip IDs and creation date.",
            "Send the best output back to OpenClaw for rewrite, extension, release metadata, or video prompt work.",
        ],
    )


def render_markdown(pack: SongPack) -> str:
    lines = [
        f"# {pack.title}",
        "",
        "## Suno Custom Mode",
        f"- Title: {pack.title}",
        f"- Style: {pack.suno_style}",
        f"- Negative tags: {pack.negative_tags}",
        "",
        "## Prompt",
        pack.suno_prompt,
        "",
        "## Lyrics",
        "```text",
        pack.lyrics,
        "```",
        "",
        "## Variants",
    ]
    for variant in pack.variants:
        lines.extend(
            [
                f"### {variant.name}",
                f"- Style: {variant.style}",
                f"- Prompt: {variant.prompt}",
                "",
            ]
        )
    lines.extend(["## Workflow", *[f"{idx}. {step}" for idx, step in enumerate(pack.workflow, 1)]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Suno Pro song production pack.")
    parser.add_argument("--theme", required=True, help="Song concept or story.")
    parser.add_argument("--genre", default="modern pop")
    parser.add_argument("--mood", default="emotional, hopeful")
    parser.add_argument("--language", default="English")
    parser.add_argument("--vocal", default="male")
    parser.add_argument("--use-case", default="social media and streaming release")
    parser.add_argument("--title", default="")
    parser.add_argument("--negative", default=DEFAULT_NEGATIVE)
    parser.add_argument("--lyrics", default="", help="Exact lyrics to use instead of generated template.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", help="Write markdown or JSON to this path.")
    args = parser.parse_args()

    pack = build_pack(args)
    if args.json:
        payload = json.dumps(asdict(pack), ensure_ascii=False, indent=2)
    else:
        payload = render_markdown(pack)

    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
