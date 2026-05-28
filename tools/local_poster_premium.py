#!/usr/bin/env python3
"""Premium local poster renderer: HTML/CSS -> Playwright screenshot -> JPG.

This complements local_poster_generator.py:
- Pillow script = fast deterministic renderer.
- This script = more maintainable Canva-like HTML/CSS renderer.
"""

from __future__ import annotations

import argparse
import base64
import html
import mimetypes
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from local_photo_enhance import enhance_image
from poster_layout_guard import analyze_image
from local_ai_copy import generate as generate_ai_copy
from local_color_palette import extract_palette


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FONT_REG = ROOT / "assets/fonts/NotoSansCJKsc-Regular.otf"
FONT_BOLD = ROOT / "assets/fonts/NotoSansCJKsc-Bold.otf"
PLAYWRIGHT_LIBS = ROOT / "vendor/playwright-libs/lib"


PRESETS = {
    "food": {
        "title": "一碗热汤的温度",
        "subtitle": "藏着最朴实的用心",
        "body": "热气升起，是熟悉的老味道；一勺一碗，都是认真生活的坚持。",
        "badge": "现煮现做 · 暖心好味道",
        "footer": "用心熬出日常里的小幸福",
        "accent": "#c95d27",
        "accent2": "#f0ad43",
    },
    "teacher": {
        "title": "教师节快乐",
        "subtitle": "一份甜甜的心意，献给用心付出的老师们",
        "body": "今天的笑容很温暖，手中的蛋糕很甜。感谢每一位老师的耐心、关怀与坚持，因为有你们，孩子的成长路上多了一份光。",
        "badge": "感恩有您 · 一路同行",
        "footer": "温暖 · 感恩 · 值得",
        "accent": "#b45f2b",
        "accent2": "#e9a83d",
    },
    "community": {
        "title": "温暖在身边",
        "subtitle": "每一份用心，都值得被看见",
        "body": "平凡的日常里，藏着最真诚的付出。一个笑容、一份心意，都让这个时刻更有温度。",
        "badge": "用心付出 · 温暖同行",
        "footer": "记录值得被记得的瞬间",
        "accent": "#b45f2b",
        "accent2": "#e9a83d",
    },
}


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def font_face(path: Path, family: str, weight: int) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"""
    @font-face {{
      font-family: '{family}';
      src: url(data:font/otf;base64,{encoded}) format('opentype');
      font-weight: {weight};
      font-style: normal;
    }}
    """


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def build_html(image: Path, copy: dict[str, str], layout: str, photo_position: str | None = None) -> str:
    portrait_position = photo_position or "52% 42%"
    if layout == "portrait-blessing":
        return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=1080,height=1620,initial-scale=1" />
<style>
{font_face(FONT_REG, "NotoCJK", 400)}
{font_face(FONT_BOLD, "NotoCJK", 700)}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  font-family: "NotoCJK", sans-serif;
  background: #11100d;
}}
.poster {{
  position: relative;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  color: #fff7e6;
  background: #14110d;
}}
.photo {{
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(180deg, rgba(11, 10, 8, .04) 0%, rgba(11, 10, 8, .03) 42%, rgba(11, 10, 8, .50) 78%, rgba(11, 10, 8, .78) 100%),
    url("{data_uri(image)}");
  background-size: cover;
  background-position: {portrait_position};
  filter: brightness(1.08) contrast(1.03) saturate(.98);
}}
.soft-panel {{
  position: absolute;
  left: 52px;
  right: 52px;
  bottom: 54px;
  padding: 44px 54px 42px;
  border-radius: 30px;
  background: rgba(18, 16, 12, .68);
  border: 1px solid rgba(255, 235, 190, .32);
  box-shadow: 0 24px 60px rgba(0, 0, 0, .38);
  backdrop-filter: blur(10px);
}}
.badge {{
  display: inline-flex;
  padding: 10px 22px 13px;
  border-radius: 999px;
  color: #ffe0a2;
  background: rgba(255, 244, 221, .10);
  border: 1px solid rgba(255, 224, 162, .40);
  font-size: 27px;
  font-weight: 700;
  margin-bottom: 22px;
}}
.title {{
  margin: 0;
  max-width: 860px;
  color: #fff6de;
  font-size: 82px;
  line-height: 1.05;
  font-weight: 700;
  text-shadow: 0 5px 18px rgba(0, 0, 0, .55);
}}
.subtitle {{
  margin: 20px 0 0;
  color: #ffd98a;
  font-size: 39px;
  line-height: 1.28;
  font-weight: 700;
}}
.rule {{
  width: 230px;
  height: 7px;
  border-radius: 999px;
  margin: 28px 0 26px;
  background: linear-gradient(90deg, #ffe3a0, rgba(255, 227, 160, 0));
}}
.body {{
  margin: 0;
  max-width: 880px;
  color: rgba(255, 248, 230, .92);
  font-size: 34px;
  line-height: 1.52;
}}
.footer {{
  margin-top: 28px;
  color: rgba(255, 225, 170, .82);
  font-size: 27px;
  letter-spacing: 0;
}}
.corner {{
  position: absolute;
  left: 52px;
  top: 54px;
  padding: 10px 20px 13px;
  border-radius: 999px;
  background: rgba(13, 12, 10, .46);
  border: 1px solid rgba(255, 235, 190, .28);
  color: rgba(255, 242, 214, .88);
  font-size: 24px;
  font-weight: 700;
  backdrop-filter: blur(8px);
}}
</style>
</head>
<body>
  <main class="poster">
    <div class="photo"></div>
    <div class="corner">YOUTH · HOPE · LIGHT</div>
    <section class="soft-panel">
      <div class="badge">{esc(copy["badge"])}</div>
      <h1 class="title">{esc(copy["title"])}</h1>
      <p class="subtitle">{esc(copy["subtitle"])}</p>
      <div class="rule"></div>
      <p class="body">{esc(copy["body"])}</p>
      <div class="footer">{esc(copy["footer"])}</div>
    </section>
  </main>
</body>
</html>
"""

    if layout == "natural-cover":
        return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=1080,height=1620,initial-scale=1" />
<style>
{font_face(FONT_REG, "NotoCJK", 400)}
{font_face(FONT_BOLD, "NotoCJK", 700)}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  font-family: "NotoCJK", sans-serif;
  background: #f3e2c7;
}}
.poster {{
  position: relative;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  color: #4a2410;
  background: #f5e5cd;
}}
.photo {{
  position: absolute;
  left: 46px;
  top: 46px;
  width: 988px;
  height: 1146px;
  border-radius: 40px;
  overflow: hidden;
  box-shadow: 0 18px 42px rgba(61, 34, 18, .26);
  background-image: url("{data_uri(image)}");
  background-size: cover;
  background-position: {portrait_position};
  filter: brightness(1.02) contrast(1.01) saturate(1.0);
}}
.photo::after {{
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(255,255,255,.02) 0%, rgba(255,255,255,0) 50%, rgba(72,37,17,.32) 100%),
    linear-gradient(90deg, rgba(0,0,0,.08) 0%, rgba(0,0,0,0) 32%, rgba(0,0,0,.06) 100%);
}}
.tag {{
  position: absolute;
  left: 88px;
  top: 92px;
  padding: 12px 26px 15px;
  border-radius: 999px;
  background: rgba(255, 248, 229, .88);
  border: 1px solid rgba(156, 95, 46, .36);
  color: #6b3216;
  font-size: 28px;
  font-weight: 700;
  box-shadow: 0 8px 22px rgba(70, 40, 21, .18);
}}
.headline {{
  position: absolute;
  left: 82px;
  right: 82px;
  top: 1018px;
  color: #fff8e7;
  text-shadow: 0 4px 14px rgba(0,0,0,.44);
}}
.headline .eyebrow {{
  font-size: 31px;
  font-weight: 700;
  color: #ffe4a3;
  margin-bottom: 16px;
}}
.headline h1 {{
  margin: 0;
  font-size: 76px;
  line-height: 1.08;
  font-weight: 700;
  max-width: 850px;
}}
.panel {{
  position: absolute;
  left: 46px;
  right: 46px;
  bottom: 48px;
  min-height: 348px;
  padding: 44px 52px 42px;
  border-radius: 36px;
  background: #fff4df;
  border: 2px solid rgba(193, 126, 58, .42);
  box-shadow: 0 18px 38px rgba(75, 43, 22, .22);
}}
.subtitle {{
  margin: 0 0 20px;
  color: #9a4b1e;
  font-size: 36px;
  line-height: 1.26;
  font-weight: 700;
}}
.body {{
  margin: 0;
  color: #4d3829;
  font-size: 34px;
  line-height: 1.48;
  max-width: 870px;
}}
.footer-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-top: 28px;
}}
.footer {{
  color: #836046;
  font-size: 25px;
}}
.seal {{
  flex: 0 0 auto;
  padding: 13px 28px 17px;
  border-radius: 999px;
  background: #a84f1f;
  color: #fff6df;
  font-size: 28px;
  font-weight: 700;
}}
</style>
</head>
<body>
  <main class="poster">
    <div class="photo"></div>
    <div class="tag">{esc(copy["badge"])}</div>
    <section class="headline">
      <div class="eyebrow">{esc(copy["subtitle"])}</div>
      <h1>{esc(copy["title"])}</h1>
    </section>
    <section class="panel">
      <p class="subtitle">{esc(copy["subtitle"])}</p>
      <p class="body">{esc(copy["body"])}</p>
      <div class="footer-row">
        <div class="footer">{esc(copy["footer"])}</div>
        <div class="seal">{esc(copy["badge"])}</div>
      </div>
    </section>
  </main>
</body>
</html>
"""

    if layout == "editorial-cover":
        return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=1080,height=1620,initial-scale=1" />
<style>
{font_face(FONT_REG, "NotoCJK", 400)}
{font_face(FONT_BOLD, "NotoCJK", 700)}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  font-family: "NotoCJK", sans-serif;
  background: #160903;
}}
.poster {{
  position: relative;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  color: #fff7df;
  background: #140802;
}}
.photo {{
  position: absolute;
  inset: 0;
  background-image: url("{data_uri(image)}");
  background-size: cover;
  background-position: {portrait_position};
  filter: brightness(1.08) contrast(1.13) saturate(1.1);
  transform: scale(1.01);
}}
.tone {{
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(18,7,2,.34) 0%, rgba(18,7,2,.03) 34%, rgba(18,7,2,.22) 100%),
    linear-gradient(180deg, rgba(0,0,0,.08) 0%, rgba(0,0,0,.02) 36%, rgba(26,8,2,.78) 72%, rgba(18,6,1,.98) 100%),
    radial-gradient(circle at 82% 8%, rgba(255,202,96,.24), transparent 24%),
    radial-gradient(circle at 16% 75%, rgba(230,83,24,.34), transparent 28%);
}}
.border {{
  position: absolute;
  inset: 38px;
  border: 4px solid rgba(255,235,188,.72);
  border-radius: 44px;
  box-shadow: inset 0 0 0 1px rgba(104,46,17,.5), 0 0 42px rgba(0,0,0,.18);
}}
.brand {{
  position: absolute;
  left: 74px;
  top: 70px;
  display: flex;
  align-items: center;
  gap: 18px;
  color: #fff4c8;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 3px 12px rgba(0,0,0,.55);
}}
.brand::before {{
  content: "";
  width: 64px;
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffe59b, #d85b20);
  box-shadow: 0 4px 10px rgba(0,0,0,.32);
}}
.vertical {{
  position: absolute;
  right: 72px;
  top: 132px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  color: rgba(255,236,190,.78);
  font-size: 25px;
  font-weight: 700;
  letter-spacing: 10px;
  text-shadow: 0 3px 10px rgba(0,0,0,.54);
}}
.headline {{
  position: absolute;
  left: 76px;
  right: 76px;
  bottom: 520px;
}}
.eyebrow {{
  display: inline-flex;
  padding: 12px 26px 16px;
  border-radius: 999px;
  color: #431908;
  background: linear-gradient(135deg, #ffe59b, #f19837);
  font-size: 31px;
  font-weight: 700;
  box-shadow: 0 12px 26px rgba(0,0,0,.35);
}}
.title {{
  margin: 26px 0 0;
  color: #fff7dd;
  font-size: 78px;
  line-height: 1.02;
  font-weight: 700;
  text-shadow: 0 8px 22px rgba(0,0,0,.72);
  max-width: 930px;
}}
.panel {{
  position: absolute;
  left: 58px;
  right: 58px;
  bottom: 58px;
  min-height: 275px;
  padding: 38px 48px 36px;
  border-radius: 34px;
  background: linear-gradient(135deg, rgba(255,246,222,.18), rgba(255,236,190,.08));
  border: 2px solid rgba(255,228,166,.42);
  box-shadow: 0 26px 54px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.22);
  backdrop-filter: blur(14px);
}}
.subtitle {{
  margin: 0 0 18px;
  color: #ffd979;
  font-size: 36px;
  line-height: 1.2;
  font-weight: 700;
  text-shadow: 0 3px 12px rgba(0,0,0,.48);
}}
.body {{
  margin: 0;
  color: rgba(255,249,232,.94);
  font-size: 35px;
  line-height: 1.43;
  max-width: 845px;
  text-shadow: 0 3px 10px rgba(0,0,0,.54);
}}
.footer-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-top: 26px;
}}
.footer {{
  color: rgba(255,232,183,.82);
  font-size: 25px;
}}
.seal {{
  flex: 0 0 auto;
  padding: 13px 28px 17px;
  border-radius: 999px;
  color: #3d1607;
  background: #ffe2a1;
  font-size: 29px;
  font-weight: 700;
}}
</style>
</head>
<body>
  <main class="poster">
    <div class="photo"></div>
    <div class="tone"></div>
    <div class="border"></div>
    <div class="brand">{esc(copy["subtitle"])}</div>
    <div class="vertical">{esc(copy["badge"])}</div>
    <section class="headline">
      <div class="eyebrow">{esc(copy["badge"])}</div>
      <h1 class="title">{esc(copy["title"])}</h1>
    </section>
    <section class="panel">
      <p class="subtitle">{esc(copy["subtitle"])}</p>
      <p class="body">{esc(copy["body"])}</p>
      <div class="footer-row">
        <div class="footer">{esc(copy["footer"])}</div>
        <div class="seal">{esc(copy["badge"])}</div>
      </div>
    </section>
  </main>
</body>
</html>
"""

    if layout == "story-cover":
        return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=1080,height=1620,initial-scale=1" />
<style>
{font_face(FONT_REG, "NotoCJK", 400)}
{font_face(FONT_BOLD, "NotoCJK", 700)}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  font-family: "NotoCJK", sans-serif;
  background: #261208;
}}
.poster {{
  position: relative;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  background: #2a150a;
}}
.poster::before {{
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("{data_uri(image)}");
  background-size: cover;
  background-position: {portrait_position};
  filter: brightness(1.05) contrast(1.08) saturate(1.08);
}}
.poster::after {{
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0,0,0,.04) 0%, rgba(0,0,0,.08) 42%, rgba(32,12,4,.68) 70%, rgba(25,8,2,.94) 100%),
    radial-gradient(circle at 80% 10%, rgba(255,199,91,.22), transparent 26%),
    radial-gradient(circle at 18% 85%, rgba(222,92,30,.28), transparent 28%);
}}
.frame {{
  position: absolute;
  inset: 44px;
  border: 5px solid rgba(255,244,218,.82);
  border-radius: 42px;
  z-index: 2;
  pointer-events: none;
}}
.top-badge {{
  position: absolute;
  z-index: 3;
  top: 76px;
  left: 72px;
  padding: 13px 28px 17px;
  border-radius: 999px;
  color: #fff8dc;
  background: rgba(115,45,15,.78);
  border: 2px solid rgba(255,224,152,.76);
  font-size: 30px;
  font-weight: 700;
  letter-spacing: .5px;
  backdrop-filter: blur(8px);
}}
.copy {{
  position: absolute;
  z-index: 3;
  left: 76px;
  right: 76px;
  bottom: 76px;
  color: #fff7df;
}}
.eyebrow {{
  color: #ffd36f;
  font-size: 34px;
  font-weight: 700;
  margin-bottom: 20px;
  text-shadow: 0 3px 12px rgba(0,0,0,.55);
}}
.title {{
  margin: 0;
  color: #fff6db;
  font-size: 96px;
  font-weight: 700;
  line-height: 1.04;
  text-shadow: 0 6px 18px rgba(0,0,0,.62);
}}
.rule {{
  width: 230px;
  height: 10px;
  margin: 30px 0 28px;
  border-radius: 999px;
  background: linear-gradient(90deg, #ffd36f, #dd6424);
  box-shadow: 0 4px 12px rgba(0,0,0,.28);
}}
.body {{
  max-width: 850px;
  margin: 0;
  color: rgba(255,250,232,.94);
  font-size: 39px;
  line-height: 1.48;
  text-shadow: 0 3px 10px rgba(0,0,0,.58);
}}
.cta {{
  display: inline-flex;
  margin-top: 34px;
  padding: 15px 42px 19px;
  border-radius: 999px;
  color: #451908;
  background: linear-gradient(135deg, #ffe09a, #f08d36);
  font-size: 34px;
  font-weight: 700;
  box-shadow: 0 12px 24px rgba(0,0,0,.34);
}}
.footer {{
  margin-top: 24px;
  color: rgba(255,238,199,.82);
  font-size: 27px;
}}
</style>
</head>
<body>
  <main class="poster">
    <div class="frame"></div>
    <div class="top-badge">{esc(copy["badge"])}</div>
    <section class="copy">
      <div class="eyebrow">{esc(copy["subtitle"])}</div>
      <h1 class="title">{esc(copy["title"])}</h1>
      <div class="rule"></div>
      <p class="body">{esc(copy["body"])}</p>
      <div class="cta">{esc(copy["badge"])}</div>
      <div class="footer">{esc(copy["footer"])}</div>
    </section>
  </main>
</body>
</html>
"""

    photo_h = "1020px" if layout == "photo-large" else "705px"
    panel_top = "1134px" if layout == "photo-large" else "830px"
    panel_h = "404px" if layout == "photo-large" else "690px"
    photo_fit = "cover"
    object_pos = photo_position or ("52% 52%" if layout == "photo-large" else "50% 42%")
    title_size = "76px" if len(copy["title"]) > 5 else "90px"
    body_size = "35px" if layout == "photo-large" else "36px"

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=1080,height=1620,initial-scale=1" />
<style>
{font_face(FONT_REG, "NotoCJK", 400)}
{font_face(FONT_BOLD, "NotoCJK", 700)}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  width: 1080px;
  height: 1620px;
  overflow: hidden;
  font-family: "NotoCJK", sans-serif;
}}
.poster {{
  position: relative;
  width: 1080px;
  height: 1620px;
  background:
    radial-gradient(circle at 0% 0%, rgba(255,201,82,.62) 0 180px, transparent 181px),
    radial-gradient(circle at 100% 13%, rgba(255,139,106,.48) 0 185px, transparent 186px),
    radial-gradient(circle at 94% 96%, rgba(255,201,82,.42) 0 210px, transparent 211px),
    linear-gradient(180deg, #ffe4bd 0%, #fff4df 45%, #ffdcae 100%);
}}
.poster::before {{
  content: "";
  position: absolute;
  inset: 0;
  background-image: url("{data_uri(image)}");
  background-size: cover;
  background-position: {object_pos};
  filter: blur(28px) brightness(.7) saturate(1.08);
  opacity: .32;
  transform: scale(1.07);
}}
.photo-card {{
  position: absolute;
  left: 70px;
  top: 70px;
  width: 940px;
  height: {photo_h};
  border: 8px solid rgba(255,250,235,.96);
  border-radius: 44px;
  overflow: hidden;
  box-shadow: 0 24px 40px rgba(63,35,15,.38);
  background: #fff6e8;
}}
.photo-card img {{
  width: 100%;
  height: 100%;
  object-fit: {photo_fit};
  object-position: {object_pos};
  filter: brightness(1.05) contrast(1.06) saturate(1.04);
}}
.panel {{
  position: absolute;
  left: 70px;
  top: {panel_top};
  width: 940px;
  height: {panel_h};
  padding: 48px 72px 42px;
  border-radius: 38px;
  border: 3px solid rgba(220,146,65,.8);
  background: rgba(255,250,238,.95);
  box-shadow: 0 16px 28px rgba(130,70,26,.22);
  display: flex;
  flex-direction: column;
  align-items: center;
}}
.title {{
  color: #813b19;
  font-size: {title_size};
  font-weight: 700;
  line-height: 1.05;
  text-align: center;
  margin: 0;
}}
.subtitle {{
  color: {copy["accent"]};
  font-size: 39px;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
  margin: 12px 0 16px;
}}
.rule {{
  width: 520px;
  height: 9px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, {copy["accent2"]}, transparent);
  margin-bottom: 30px;
}}
.body {{
  color: #4f3a2b;
  font-size: {body_size};
  line-height: 1.5;
  text-align: center;
  max-width: 800px;
  margin: 0;
}}
.badge {{
  margin-top: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 64px;
  padding: 8px 46px 12px;
  border-radius: 999px;
  color: #fffdf1;
  background: linear-gradient(135deg, {copy["accent"]}, #d46c2a);
  font-size: 34px;
  font-weight: 700;
  box-shadow: inset 0 -3px 0 rgba(0,0,0,.12);
}}
.footer {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 30px;
  text-align: center;
  color: rgba(112,76,49,.88);
  font-size: 27px;
}}
</style>
</head>
<body>
  <main class="poster">
    <section class="photo-card"><img src="{data_uri(image)}" /></section>
    <section class="panel">
      <h1 class="title">{esc(copy["title"])}</h1>
      <div class="subtitle">{esc(copy["subtitle"])}</div>
      <div class="rule"></div>
      <p class="body">{esc(copy["body"])}</p>
      <div class="badge">{esc(copy["badge"])}</div>
    </section>
    <div class="footer">{esc(copy["footer"])}</div>
  </main>
</body>
</html>
"""


def render_with_playwright(html_path: Path, png_path: Path) -> None:
    cmd = [
        "pnpm",
        "playwright",
        "screenshot",
        "--browser",
        "chromium",
        "--viewport-size",
        "1080,1620",
        "--wait-for-timeout",
        "500",
        html_path.resolve().as_uri(),
        str(png_path),
    ]
    env = os.environ.copy()
    if PLAYWRIGHT_LIBS.exists():
        existing = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = str(PLAYWRIGHT_LIBS) + (f":{existing}" if existing else "")
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=60, env=env)
    if proc.returncode == 0:
        return
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    if "Executable doesn't exist" in combined or "playwright install" in combined:
        raise SystemExit(
            "Playwright Chromium browser is not installed. Run:\n"
            "  npx playwright install chromium\n\n"
            + combined
        )
    if "error while loading shared libraries" in combined:
        raise SystemExit(
            "Playwright Chromium is missing Linux runtime libraries. "
            "Install system deps or extract them to vendor/playwright-libs/lib.\n\n"
            + combined
        )
    raise SystemExit(combined)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a premium poster using local HTML/CSS + Playwright.")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--style", choices=sorted(PRESETS), default="community")
    parser.add_argument("--layout", choices=["photo-large", "balanced", "story-cover", "editorial-cover", "natural-cover", "portrait-blessing"], default="photo-large")
    parser.add_argument("--title")
    parser.add_argument("--subtitle")
    parser.add_argument("--body")
    parser.add_argument("--badge")
    parser.add_argument("--footer")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--keep-html", action="store_true")
    parser.add_argument("--enhance", action="store_true", help="Run local OpenCV/Pillow photo enhancement before rendering.")
    parser.add_argument("--enhance-preset", choices=["poster", "food", "portrait", "soft", "p53"], default="poster")
    parser.add_argument("--enhance-strength", type=float, default=1.0)
    parser.add_argument("--photo-position", help="CSS background/object position, e.g. '50% 38%'.")
    parser.add_argument("--auto-photo-position", action="store_true", help="Analyze the photo and keep the main subject in a safer crop.")
    parser.add_argument("--ai-copy", action="store_true", help="Generate copy using local Qwen 3.5.")
    parser.add_argument("--ai-copy-hint", default="", help="Extra hint for AI copy generation.")
    parser.add_argument("--ai-copy-language", choices=["cn", "en", "bm"], default="cn", help="Language for AI-generated copy.")
    parser.add_argument("--auto-color", action="store_true", help="Extract dominant color palette from source photo.")
    args = parser.parse_args()

    if not FONT_REG.exists() or not FONT_BOLD.exists():
        raise SystemExit("Missing NotoSansCJKsc fonts under assets/fonts/.")
    if not args.image.exists():
        raise SystemExit(f"Image not found: {args.image}")

    copy = dict(PRESETS[args.style])
    for key in ("title", "subtitle", "body", "badge", "footer"):
        value = getattr(args, key)
        if value:
            copy[key] = value

    # P5.11: AI copy generation (overrides presets unless CLI args also passed)
    if args.ai_copy:
        ai_result = generate_ai_copy(
            scene_type=args.style,
            language=args.ai_copy_language,
            hint=args.ai_copy_hint,
        )
        for key in ("title", "subtitle", "body", "badge", "footer"):
            cli_val = getattr(args, key)
            if not cli_val:  # Only override if user didn't pass explicit --flag
                copy[key] = getattr(ai_result, key)
        if ai_result.warnings:
            print(f"ai_copy warnings: {ai_result.warnings}")
        print(f"ai_copy source={ai_result.raw_output[:60]}... language={ai_result.language}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = args.output or REPORTS / f"premium_poster_{args.style}_{timestamp}.jpg"
    output = output.resolve()
    png_path = output.with_suffix(".png")
    render_image = args.image.resolve()

    if args.enhance:
        enhanced_dir = REPORTS / "enhanced"
        enhanced_path = enhanced_dir / f"{args.image.stem}_enhanced_{timestamp}.jpg"
        result = enhance_image(args.image.resolve(), enhanced_path, args.enhance_preset, args.enhance_strength)
        render_image = Path(str(result["output"])).resolve()
        print(
            f"enhanced={render_image} preset={result['preset']} strength={result['strength']} "
            f"luma={result['mean_luma_before']}->{result['mean_luma_after']}"
        )

    photo_position = args.photo_position
    if args.auto_photo_position:
        analysis = analyze_image(render_image, args.layout)
        photo_position = analysis.recommended_position
        warning_text = ",".join(analysis.warnings) if analysis.warnings else "none"
        print(
            f"layout_guard position={photo_position} faces={analysis.face_count} "
            f"text_zone_risk={analysis.text_zone_risk} warnings={warning_text}"
        )

    # P5.12: Auto color palette extraction
    if args.auto_color:
        palette = extract_palette(render_image, args.style)
        copy["accent"] = palette["accent_hex"]
        copy["accent2"] = palette["accent2_hex"]
        copy["bg_hex"] = palette["bg_hex"]
        copy["bg_dark_hex"] = palette["bg_dark_hex"]
        print(
            f"auto_color accent={palette['accent_hex']} accent2={palette['accent2_hex']} "
            f"palette_type={palette['palette_type']} dominants={palette['dominant_colors_hex']}"
        )

    html_content = build_html(render_image, copy, args.layout, photo_position)
    if args.keep_html:
        html_path = output.with_suffix(".html")
        html_path.write_text(html_content, encoding="utf-8")
    else:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
        tmp.write(html_content)
        tmp.close()
        html_path = Path(tmp.name)

    try:
        render_with_playwright(html_path, png_path)
        with Image.open(png_path) as img:
            img.convert("RGB").save(output, quality=94, subsampling=1)
    finally:
        if not args.keep_html:
            html_path.unlink(missing_ok=True)

    print(output)


if __name__ == "__main__":
    main()
