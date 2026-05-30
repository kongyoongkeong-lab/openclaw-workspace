# MEMORY.md — Jason / OpenClaw Long-Term Memory

Purpose: curated high-signal memory for Jason's OpenClaw/Pentagon system. This file should contain stable facts only, not raw logs or transient runtime noise.

## Jason Profile
- Jason is the system owner / principal engineer for this OpenClaw workspace.
- Correct home path: `/home/jason2ykk/`.
- OpenClaw workspace: `/home/jason2ykk/.openclaw/workspace/`.
- Jason prefers direct, technical, data-driven answers with minimal fluff.
- Jason values production-grade execution, verifiable outputs, automation, and local-first control.

## Long-Term Goal
- Build a Jason-version JARVIS: a personal AI operating system / orchestration layer that understands short commands, invokes tools, coordinates agents, automates workflows, and reports status.
- Pentagon Team is the operating metaphor: `@main` orchestrates, `@intel` researches, `@ops` executes, `@comms` formats/communicates, `@sentinel` guards/security-checks.

## Stable Preferences
- Communication: concise, direct, technical, data-driven.
- Coding: prefers Python for data workflows and Node.js for systems; prefers `pnpm` over `npm`.
- Execution: default production model strategy is Hybrid Mode: API/main orchestrates long-context/tool-heavy work; local qwen handles compact/private reasoning and GPU-worker tasks when VRAM is safe.
- Reporting: task completions should include what was done, evidence/verification, and agent/time summary when appropriate.

## Active Shortcuts
- `指令列表`: read `/home/jason2ykk/.openclaw/workspace/shortcuts.md` and return the shortcut table.
- `今日新闻` / `每日新闻` / `daily news`: run the daily news workflow, cache-first; if `daily_news.md` is missing, rebuild workflow before execution.
- `今日AI` / `今日 AI` / `AI日报` / `最新AI动态`: run the AI daily workflow; if `daily_ai.md` is missing, rebuild workflow before execution.
- `额度查询`: run `/home/jason2ykk/.openclaw/workspace/tools/quota_query.py` only after confirming the script exists; never expose tokens/secrets.
- `额度切换` / `Codex切换` / `账号切换`: run quota profile preflight only after confirming the script exists; never expose tokens/secrets.
- `塔维切换` / `Tavily切换` / `搜索切换` / `塔维账号`: run Tavily key preflight only after confirming the script exists; never expose API keys.
- `当前模式`: run `/home/jason2ykk/.openclaw/workspace/tools/protocol_mode_state.py get`.
- `架构模式`: run `/home/jason2ykk/.openclaw/workspace/tools/protocol_mode_state.py set architect_mode --source shortcut`.
- `稳定模式`: run `/home/jason2ykk/.openclaw/workspace/tools/protocol_mode_state.py set stable --source shortcut`.
- `API模型`: prefer API-first routing for orchestration, tool-heavy, and long-context work; local remains fallback.
- `本地模型`: prefer local GPU/Ollama routing for compact, private, direct reasoning; API remains fallback; check VRAM before local LLM use.
- `混合模型`: default recommended strategy; API orchestrates and local qwen handles compact reasoning/private summarization/GPU-worker tasks.
- `当前模型`: show active model/fallback/quota/routing status via session status.
- `模型策略`: summarize `/home/jason2ykk/.openclaw/workspace/docs/model_runtime_strategy.md`.
- `上下文预算`: run `/home/jason2ykk/.openclaw/workspace/tools/api_context_budget.py`; use `--current-session` when Jason asks about the active session.
- `路由决策`: run `/home/jason2ykk/.openclaw/workspace/tools/model_route_decision.py` with the relevant task type.
- `服务检查` / `系统检查`: check gateway/model status, Docker services, Redis, Qdrant, and ComfyUI health in read-only mode.
- `GitHub状态` / `仓库状态`: inspect git/gh remote status without push/merge unless explicitly requested.
- `系统备份`: use the `openclaw-backup` skill; requires explicit confirmation because backups include sensitive data.

## Durable Workflow Rules
- Daily news must check today's archive first. If an archive exists and is within 6 hours, return cached report immediately without DDG/Tavily/web_fetch.
- Daily news refresh/re-crawl only when Jason explicitly says: `刷新新闻`, `重新抓取`, `重新生成今日新闻`, `deep search`, or `深度搜索`.
- Shortcut registry lives in `/home/jason2ykk/.openclaw/workspace/shortcuts.md`; keep it updated when new 4-character Chinese shortcuts are confirmed.

## Safety / Privacy
- Do not store Telegram bot token, Tavily key, OpenAI key, passwords, access tokens, or raw secrets in memory.
- For security-sensitive actions such as token rotation, hardening, backups, destructive writes, production activation, new agents, or persistent background tasks, ask for explicit confirmation.

## Memory Hygiene
- Root `MEMORY.md` is for stable curated facts.
- Daily/runtime logs belong under `memory/logs/YYYY-MM-DD.md`; existing
  `memory/YYYY-MM-DD.md` files are legacy logs kept for retrieval continuity.
- Preferences belong under `memory/preferences/`.
- Architecture decisions belong under `memory/decisions/`.
- Stable execution rules belong under `memory/system/stable_rules.md`.
- Project context belongs under `memory/projects/<project>/`.
- Chat/group context belongs under `memory/groups/<surface>/`.
- Candidate memories awaiting verification belong under `memory/review/`.
- Old experiments and validation reports should eventually be archived to reduce retrieval noise.

## Structured Memory Files
- User preferences: `/home/jason2ykk/.openclaw/workspace/memory/preferences/jason.md`.
- Architecture/workflow decisions: `/home/jason2ykk/.openclaw/workspace/memory/decisions/openclaw.md`.
- Stable operational rules: `/home/jason2ykk/.openclaw/workspace/memory/system/stable_rules.md`.
- Memory contract: `/home/jason2ykk/.openclaw/workspace/memory/system/memory_contract.md`.

## GitHub Memory Guidance
- Repository-wide GitHub Copilot guidance lives in `.github/copilot-instructions.md`.
- Path-specific memory guidance lives in `.github/instructions/memory.instructions.md`.
- `AGENTS.md` remains the agent runtime behavior contract.
