# Pentagon Capability Map

Status: active baseline
Owner: Jason / Pentagon `@main`
Last updated: 2026-05-25
Scope: `/home/jason2ykk/.openclaw/workspace`

Purpose: give `@main` a durable local routing map for tools, services, scripts, skills, workflows, safety checks, and fallback paths. This file must never contain raw tokens, passwords, cookies, API keys, or OAuth material.

## Routing Principles

- Prefer the shortest verified local path before cloud/API fallback.
- For local LLM, image, and video work, run `tools/check_gpu.sh` before starting GPU-heavy jobs.
- Keep local GPU work below 9,728 MiB VRAM unless Jason explicitly approves a monitored exception.
- Use API-first routing for long-context, current-knowledge, tool-heavy orchestration, and final synthesis.
- Use local/Ollama routing for compact private reasoning, classification, summarization, embeddings, and low-risk worker tasks.
- Use artifacts for large outputs: `shared/artifacts/`, `shared/specs/`, `shared/reviews/`, `reports/`, `docs/`, and `memory/`.
- Do not expose public tunnels, rotate tokens, write Qdrant, start persistent background jobs, or activate production-facing workflows without explicit approval.

## Core Agents

| Agent | Role | Workspace | Primary Deliverables | Review Gate |
|---|---|---|---|---|
| `@main` | Orchestrator, routing, synthesis, task lifecycle | workspace root | final decisions, task state, memory updates | self-check + sentinel for sensitive work |
| `@intel` | Research, web/file parsing, citation-backed findings | `intel/` | `shared/specs/` | `@sentinel` research review |
| `@ops` | Shell, Python, Docker, browser/CDP automation, build execution | `ops/` | `shared/artifacts/` | `@sentinel` build review |
| `@comms` | Formatting, packaging, delivery | `comms/` | `shared/reports/` | `@intel` accuracy review |
| `@sentinel` | Security, hallucination checks, VRAM/build guard | `sentinel/` | `shared/reviews/` | `@ops` reviews sentinel scripts |

## Active Services

| Service | Purpose | Endpoint / Port | Health Check | Notes |
|---|---|---|---|---|
| n8n | Local workflow automation and webhooks | `http://localhost:5678` | `curl http://localhost:5678/healthz` | Docker stack in `n8n/`; images pinned to `2.21.7` |
| n8n runner | External code execution runner for n8n | internal Docker network | `docker compose ps` in `n8n/` | paired with n8n |
| n8n PostgreSQL | n8n data store | Docker internal `5432` | Docker healthcheck | credentials in `n8n/.env`, do not print |
| Langfuse | Observability and eval traces | `http://localhost:3000` | `docker ps`, `tools/observability.py --query` | stack in `docker/langfuse/` |
| Redis | Queue/cache layer | `127.0.0.1:6379` | `redis-cli ping` if available | container name `redis` |
| Qdrant | Vector memory / vault backend | `127.0.0.1:6333` | `curl http://localhost:6333/collections` | writes require explicit approval unless workflow grants it |
| ComfyUI | Local image/video pipeline endpoint | `127.0.0.1:8188` | `curl http://127.0.0.1:8188/system_stats` | check VRAM before generation |
| cloudflared | Public tunnel client | local binary only | `tools/bin/cloudflared --version` | binary installed; tunnel not started by default |

## Workflows

| Workflow | Trigger | Path / Endpoint | Status | Verification |
|---|---|---|---|---|
| Daily News | `今日新闻`, `每日新闻`, `daily news` | `daily_news.md`, archive `news/YYYY-MM-DD_daily_news.md` | active | cache-first, refresh only on explicit refresh commands |
| AI Daily News | `今日AI`, `AI日报`, `最新AI动态` | `daily_ai.md`, archive `news/ai/` | active | search last 7 days, cite dates/sources |
| Automation Protocol | `自动协议`, `automation-protocol` | `skills/automation-protocol/SKILL.md` | active | CDP/Playwright first; output path/size/timestamp verification |
| PDF to PPTX via browser | `PDF转PPT`, `pdf2pptx` | `automation-protocol`; `/mnt/c/Users/jason/OpenClaw/tools/pdf2pptx_convert.mjs` | active | upload, convert, download, verify `.pptx` |
| PDF to PPTX intake | n8n webhook | `POST http://localhost:5678/webhook/pdf-to-pptx` | intake active, conversion pending | returns JSON status and target output path |
| Model Mode | `API模型`, `本地模型`, `混合模型` | `tools/model_mode_state.py` | active | workspace-local state only |
| Protocol Mode | `架构模式`, `稳定模式`, `当前模式` | `tools/protocol_mode_state.py` | active | no production activation by mode switch alone |
| Quota Check | `额度查询` | `tools/quota_query.py` | active | no token output |
| Codex Profile Preflight | `额度切换`, `Codex切换`, `账号切换` | `tools/codex_quota_preflight.py` | active | no token output |
| Tavily Key Preflight | `塔维切换`, `Tavily切换`, `搜索切换`, `塔维账号` | `tools/tavily_key_preflight.py --check-all` | active, key currently required | no key output |
| System Check | `服务检查`, `系统检查` | `tools/system_health_check.py`, `docs/system_health_check.md` | active | read-only unless explicitly asked |
| GitHub Status | `GitHub状态`, `仓库状态` | `git status`, `gh repo view` | active | no push/pull/merge unless explicitly requested |

## Tool Capability Groups

### System, Routing, and Runtime

| Capability | Primary Tool | Health / Verify | Fallback |
|---|---|---|---|
| GPU preflight | `tools/check_gpu.sh` | command exits and reports VRAM | avoid local GPU jobs |
| Model routing mode | `tools/model_mode_state.py` | `get` command | read `config/model_runtime.json` |
| Runtime status | `tools/model_runtime_status.py` | prints safe snapshot | `session_status` tool |
| System health report | `tools/system_health_check.py` | gateway/Docker/n8n/Redis/Qdrant/ComfyUI/Langfuse/model/GPU/disk report | manual command bundle |
| Route decision | `tools/model_route_decision.py` | task-type decision output | manual hybrid policy |
| API context budget | `tools/api_context_budget.py` | budget table | `docs/model_runtime_strategy.md` |
| Protocol mode | `tools/protocol_mode_state.py` | `get` command | stable mode |
| Quota snapshot | `tools/quota_query.py` | safe quota table | manual account check |
| Hugging Face preflight | `tools/huggingface_preflight.py`, `docs/huggingface_setup.md` | CLI/token/model-access status | manual download/browser login |
| Hugging Face safe download | `tools/huggingface_download.py`, `docs/huggingface_setup.md` | plan-only probe; actual download requires `--yes` | manual `hf download` |
| Codex profile order | `tools/codex_quota_preflight.py` | dry-run/check output | leave existing order unchanged |

### Search, Research, and Memory

| Capability | Primary Tool / Skill | Secret Needed | Fallback |
|---|---|---|---|
| Tavily search | `tools/tavily_key_preflight.py`, `tavily-search` skill | `TAVILY_API_KEY` or `TAVILY_KEYS` | DDG/multi-search skill |
| No-key search | `ddg-search`, `multi-search-engine` skills | no | browser/manual source fetch |
| Memory extraction | `tools/memory_extract.py` | no | manual update to `MEMORY.md` |
| Stable memory | `MEMORY.md`, `memory/preferences/`, `memory/decisions/`, `memory/system/` | no | ask Jason before changing durable facts |
| Vector memory | Qdrant | maybe embeddings/model config | file memory when writes are not approved |

### Automation, Browser, and Windows Control

| Capability | Primary Tool | Health / Verify | Fallback |
|---|---|---|---|
| Local automation router | `tools/automation_router.py` | command-specific dry run/status | direct PowerShell/UIA/AHK |
| Browser CDP smoke | `tools/playwright_cdp_smoke.js`, `tools/playwright_cdp_smoke_windows.mjs` | CDP at `127.0.0.1:9222` | browser skill / manual |
| Automation protocol skill | `skills/automation-protocol/` | `python3 .../skill-creator/scripts/quick_validate.py skills/automation-protocol` | manual CDP/PowerShell steps |
| Automation file probe | `skills/automation-protocol/scripts/automation_file_probe.py` | `find <name>` and `verify <path> --suffix <ext>` | PowerShell `Get-ChildItem` / `Get-Item` |
| Doubao CDP automation | `tools/doubao_cdp_controller.js`, `tools/doubao_cdp_probe.js`, `tools/doubao_submit_video.js` | persistent Chrome profile active | manual browser |
| Gemini CDP video | `tools/gemini_cdp_video.mjs` | CDP active and logged in | manual browser |
| Windows UI automation | `tools/windows_ui/` | Windows bridge checks | AHK / manual |

### PDF, Documents, OCR, and Summaries

| Capability | Primary Tool / Skill | Health / Verify | Fallback |
|---|---|---|---|
| PDF preflight/routing | `tools/pdf_intake.py` | JSON route output | `pdf` skill |
| PDF quality gate | `tools/pdf_quality_gate.py` | gate pass/fail | manual inspection |
| OCR via OCR.Space | `tools/ocr_space.py` | response contains parsed text | `image-ocr` / local Tesseract |
| Local summarization | `summarize-pro` skill | file summary output | API summary with privacy warning |
| Doc formatting | `doc-format-brush` skill | generated formatted document | manual Word/Markdown formatting |

### Image, Photo, Poster, and Video

| Capability | Primary Tool / Skill | Health / Verify | Fallback |
|---|---|---|---|
| Photo capability check | `tools/photo_capability_check.py` | read-only snapshot | skip advanced processing |
| Photo quality gate | `tools/photo_quality_gate.py` | deterministic metrics | manual review |
| Local photo enhancement | `tools/local_photo_enhance.py` | output image + metrics | ComfyUI enhance |
| ComfyUI photo enhance | `tools/comfy_photo_enhance.py` | ComfyUI API job success | local Pillow/OpenCV |
| ComfyUI upscale | `tools/comfy_p54_upscale.py` | output image exists | skip upscale |
| Poster generation | `tools/make_poster.py`, `tools/local_poster_generator.py`, `tools/local_poster_premium.py` | manifest/report/output image | simpler Pillow route |
| Poster gates | `tools/poster_quality_gate.py`, `tools/poster_layout_guard.py`, `tools/poster_auto_select.py`, `tools/poster_version_matrix.py` | score/report | manual selection |
| Video capability check | `tools/local_video_capability_check.py` | read-only capability report | external generation |
| Video prompt helper | `tools/phone_video_prompt.py` | prompt/ffmpeg command output | manual prompt |
| Antigravity image gen | `antigravity-image-gen` skill | generated image asset | local ComfyUI/image_gen |

### Observability and Evaluation

| Capability | Primary Tool | Health / Verify | Fallback |
|---|---|---|---|
| Langfuse traces | `tools/observability.py` | `--query` shows recent observations | write report under `reports/audit/` |
| Eval gate | `tools/eval_gate.py` | metric JSON/report | manual sentinel review |
| Capability evolution | `capability-evolver` skill | proposal artifact | `memory/errors/` failure journal |
| Self-improvement | `self-improvement` / `self-improving` skills | learning entry | manual `memory/review/` |

### GitHub, Backups, and Security

| Capability | Primary Tool / Skill | Safety Rule | Fallback |
|---|---|---|---|
| GitHub inspection | `github` skill, `gh` CLI | no push/pull/merge unless requested | `git status` only |
| Issue/PR workflows | `gh-issues` skill | dry-run first for broad changes | manual triage |
| Backup | `openclaw-backup` skill | explicit confirmation required | no backup |
| Security audit | `openclaw-security-guard` skill | do not print secrets | targeted `rg` secret scan |
| Skill vetting | `skill-vetter` skill | vet before installing external skills | do not install |

## Installed Skills

Core local skills currently available:

- `agent-browser-core`
- `agent-team-orchestration`
- `antigravity-image-gen`
- `automation-protocol`
- `api-gateway`
- `capability-evolver`
- `content-writer`
- `ddg-search`
- `doc-format-brush`
- `docker`
- `e2e-testing-patterns`
- `file-organizer-skill`
- `gh-issues`
- `github`
- `image-ocr`
- `local-whisper`
- `memory-setup`
- `model-usage-linux`
- `multi-search-engine`
- `openclaw-backup`
- `openclaw-security-guard`
- `tavily-search`
- `pdf`
- `python-executor`
- `self-evolving-skill`
- `self-improvement`
- `self-improving`
- `skill-vetter`
- `summarize-pro`
- `task-planner`
- `terminal-command-execution`
- `testing-patterns`

## Secret and Account Requirements

| Capability | Required Secret / Account | Storage Expectation | Output Rule |
|---|---|---|---|
| Tavily search | `TAVILY_API_KEY`, `TAVILY_API_KEY_*`, or `TAVILY_KEYS` | environment or `~/.openclaw/.env` | never print key |
| OpenAI/Codex quotas | Codex auth profiles | OpenClaw auth store | never print access/refresh tokens |
| n8n API | API key created in n8n UI | user-managed secret store/env | never store raw key in scripts |
| Cloudflare tunnel | Cloudflare login/token/domain | Cloudflare-managed config or env | do not expose tunnel without approval |
| Hugging Face | `HF_TOKEN` or `huggingface_hub` cache token | environment, `~/.openclaw/.env`, or `hf auth login` | never print token |
| Telegram/WhatsApp delivery | bot/app tokens | existing OpenClaw connector/gateway | never print token |
| OCR.Space | optional API key | env if upgraded from `helloworld` | never print key |

## Health Check Bundles

### Fast System Check

```bash
python3 tools/system_health_check.py
python3 tools/system_health_check.py --details
python3 tools/system_health_check.py --json
```

### n8n Workflow Check

```bash
cd /home/jason2ykk/.openclaw/workspace/n8n
docker compose ps
curl -sS http://localhost:5678/healthz
curl -sS -X POST http://localhost:5678/webhook/pdf-to-pptx \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"/data/inbox/test.pdf"}'
```

### Secret Hygiene Check

```bash
rg -n "n8n-auth=eyJ|eyJhbGci|TAVILY_API_KEY=.*[A-Za-z0-9_-]{10}|OPENAI_API_KEY=.*[A-Za-z0-9_-]{10}" \
  n8n tools . --glob '!node_modules' --glob '!memory/**'
```

## Known Gaps

- Tavily key is not configured yet; `tools/tavily_key_preflight.py --check-all` reports no key.
- Hugging Face CLI/token/account auth is configured and verified for `jason2ykk`; safe model download helper is available at `tools/huggingface_download.py`; gated/private models still require per-model license/access approval.
- n8n API key must be created from the UI because raw keys are only shown at creation time.
- Cloudflare tunnel binary is installed, but no public tunnel is active by default.
- PDF to PPTX workflow currently verifies intake/response; actual conversion implementation is still pending.
- `TASKS.md` is empty and should be used for larger multi-agent work.
- Failure journal now exists in `memory/errors/`; use `tools/failure_journal.py` to add sanitized entries, update the prevention-rule index, and scan journal files for secret-like material.

## Update Rules

- Update this map when adding a new shortcut, service, workflow, tool script, skill, or external account dependency.
- Store operational procedures in `memory/procedures/` or `docs/`, then link them here.
- Store stable architecture decisions in `memory/decisions/openclaw.md`.
- Store runtime logs and transient observations outside this file.
- Never add raw secrets, bearer tokens, cookies, API keys, OAuth tokens, private keys, or passwords.
- Promote reusable failure lessons into `memory/errors/` and link them here when they affect routing.
