# Daily_AI.md — Runtime Workflow

Version: 2.0-readable-detail
Timezone: Asia/Kuala_Lumpur
Freshness: last 7 days only
Mode: Runtime Workflow
Archive path: `/home/jason2ykk/.openclaw/workspace/news/ai/`

---

## Trigger

Run when user says:

- 今日AI
- 今日 AI
- AI日报
- 最新AI动态
- daily AI
- AI news

---

## Objective

Search, verify, deduplicate, and summarize the most important **global AI news from the last 7 days only**.

The final output must be:

- easy to read on mobile
- more detailed than a headline list
- useful for engineering / business decisions
- written in clear Chinese
- grounded in verified sources
- archived as Markdown

Do **not** invent news to fill the list.

---

## Coverage Priorities

Prioritize news with real-world impact in these areas:

1. **Frontier models**
 - OpenAI, Google DeepMind / Gemini, Anthropic / Claude, Meta AI, xAI, Microsoft AI
 - new model releases, benchmark shifts, multimodal features, reasoning, coding, agents

2. **AI agents and automation**
 - coding agents, enterprise agents, orchestration/control plane, tool use, browser/computer use
 - reliability, permissioning, auditability, cost control

3. **AI hardware and infrastructure**
 - NVIDIA, AMD, Intel, Broadcom, TSMC, Samsung, SK Hynix, Micron
 - GPUs, HBM, networking, liquid cooling, power, data centers, cloud capex

4. **Enterprise adoption and business model**
 - enterprise AI spending, AI productivity, ROI, pricing, credits, usage-based billing
 - major customer deployments or pullbacks

5. **Regulation, safety, and security**
 - EU AI Act, US policy, China policy, ASEAN/Malaysia policy
 - model safety, cyber capability, deepfakes, copyright, privacy, provenance/watermarking

6. **Asia / Malaysia angle**
 - Malaysia data centers, AI talent, chips/export controls, ASEAN cloud/AI infrastructure
 - local enterprise or government AI adoption

---

## Preferred Sources

Use web search / Tavily / web fetch and prioritize reliable sources.

### Tier 1

1. Reuters
2. Associated Press
3. Bloomberg
4. Financial Times
5. Wall Street Journal
6. Official company blogs / announcements
7. Official government or regulator websites

### Tier 2

8. The Verge
9. TechCrunch
10. Ars Technica
11. MIT Technology Review
12. VentureBeat
13. CNBC
14. Nikkei Asia
15. The Information

### Tier 3

16. CNET, 9to5Google, Android Authority, Tom's Hardware, SemiAnalysis-style technical reporting
17. Local trusted sources for Malaysia / ASEAN infrastructure news

Use lower-tier sources only when the story is clearly sourced or corroborated.

---

## Search Requirements

Run multiple searches. Use a 7-day freshness filter whenever available.

Required query groups:

```text
latest AI news last 7 days global
OpenAI news last 7 days
Google DeepMind Gemini AI news last 7 days
Anthropic Claude AI news last 7 days
Meta AI xAI Microsoft AI news last 7 days
NVIDIA AMD Broadcom AI chip GPU HBM news last 7 days
AI agents coding automation enterprise news last 7 days
AI regulation safety policy news last 7 days
AI data center cloud capex power liquid cooling news last 7 days
AI semiconductor supply chain Asia Malaysia last 7 days
Malaysia AI data center cloud NVIDIA last 7 days
```

If results are weak, retry with narrower searches:

```text
site:reuters.com AI last 7 days
site:techcrunch.com AI agent last 7 days
site:theverge.com AI last 7 days
site:blogs.nvidia.com AI chip last 7 days
site:openai.com blog last 7 days
site:anthropic.com news last 7 days
site:deepmind.google news last 7 days
```

---

## Validation Gate

Drop an item if any of these apply:

- no source name
- no source URL
- no published date or clearly verified live feed timestamp
- older than 7 days in Asia/Kuala_Lumpur time
- duplicate similarity above 0.85
- pure rumor without attribution
- stock-only movement with no AI industry signal
- low-impact product marketing with no technical/business significance
- entertainment gossip or personality drama
- no clear public, technical, business, or policy impact

For paywalled sources, use only visible excerpts and avoid unsupported details.

---

## Deduplication Rules

Merge stories that describe the same event, company announcement, policy action, or market move.

When merging:

- keep the strongest source as primary
- mention corroborating sources briefly
- avoid repeating the same company story in multiple sections unless it has separate model + policy + chip impact

---

## Output Item Depth

Each selected item must include enough detail to be useful.

For every item, include:

1. **What happened** — 2–4 sentences
2. **Key details** — 2–4 bullets
3. **Why it matters** — 1–3 bullets
4. **Jason angle** — 1 short practical note for local AI / engineering / business / Malaysia relevance
5. **Source** — source name + URL

Avoid long paragraphs. Prefer short lines.

---

## Final Output Rules

- Language: Chinese
- Style: direct, technical, mobile-friendly
- Tone: readable like a sharp briefing, not academic
- Max final items: 12
- Target final items: 8–10
- Fewer is allowed if verified news is insufficient
- Use category headers
- Number only actual news items
- Number sequentially from 1
- Do not duplicate numbering
- Include a short executive summary at the top
- Include a final "今日判断" section at the bottom

---

## Output Template

```markdown
# 今日AI日报｜{{YYYY-MM-DD}}

> 范围：过去 7 天
> 时间基准：Asia/Kuala_Lumpur
> 抓取时间：{{HH:mm MYT}}
> 归档：`/home/jason2ykk/.openclaw/workspace/news/ai/{{YYYY-MM-DD}}-daily-ai.md`

## 30秒总览

- **最大主线：** {{one_sentence_main_theme}}
- **技术变化：** {{model_or_agent_change}}
- **商业变化：** {{enterprise_or_pricing_change}}
- **算力变化：** {{chip_or_infra_change}}
- **监管/风险：** {{policy_or_safety_change}}
- **马来西亚/亚洲角度：** {{local_angle}}

---

## A. 模型 / Agent

[1] 【{{title}}】

### 发生了什么
{{2-4 short sentences}}

### 关键细节
- {{detail_1}}
- {{detail_2}}
- {{detail_3}}

### 为什么重要
- {{impact_1}}
- {{impact_2}}

### Jason 角度
👉 {{practical_takeaway}}

### 来源
{{source_name}} — {{url}}

---

## B. 芯片 / 算力 / 数据中心

[2] 【{{title}}】
...

---

## C. 企业采用 / 商业模式

[3] 【{{title}}】
...

---

## D. 监管 / 安全 / 风险

[4] 【{{title}}】
...

---

## E. 亚洲 / 马来西亚

[5] 【{{title}}】
...

---

## 今日判断

1. **短期趋势：** {{trend}}
2. **值得追踪：** {{watchlist}}
3. **本地部署建议：** {{local_ai_recommendation}}
4. **风险提醒：** {{risk}}

## Sources

- {{source_1}}
- {{source_2}}
- {{source_3}}
```

---

## Archive Rules

Always write the full report to:

```text
/home/jason2ykk/.openclaw/workspace/news/ai/{{YYYY-MM-DD}}-daily-ai.md
```

If the file already exists:

- overwrite it when the user explicitly triggers 今日AI again
- keep the newest verified version
- do not create duplicate filenames unless the user asks for versions

---

## Empty State

If verified AI news is insufficient, respond:

```text
今天过去 7 天内可验证的 AI 重点新闻不足，不硬凑。
已检查：模型、芯片、Agent、监管、企业采用、亚洲/马来西亚来源。
```

---

## Quality Checklist Before Replying

Before final response, verify:

- [ ] all items are within 7 days
- [ ] every item has source URL
- [ ] no duplicate stories
- [ ] no unsupported claims from snippets
- [ ] output is easy to scan on Telegram/mobile
- [ ] archive file was written
- [ ] final reply includes archive path and condensed highlights
