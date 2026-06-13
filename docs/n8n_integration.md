# n8n Integration: OpenClaw Pentagon ↔ Workflow Automation

Protocol metadata:
- protocol_id: `n8n_integration`
- registry: `../config/protocol_registry.json`
- risk: medium
- evidence: workflow id, health status, dry-run result
- rollback: disable workflow and restore previous webhook config after approval

**Source:** [github.com/n8n-io/n8n](https://github.com/n8n-io/n8n) (190k+ stars, MIT/Sustainable Use License)
**Setup:** `n8n/docker-compose.yml` from [github.com/n8n-io/n8n-hosting](https://github.com/n8n-io/n8n-hosting)

---

## Architecture

```
┌──────────────┐     webhook (HTTP POST)     ┌──────────────────┐
│ OpenClaw     │ ──────────────────────────►  │  n8n (port 5678) │
│ (@main)      │                              │                  │
│              │◄── webhook response (JSON) ── │  Workflow Engine │
│ Sessions:    │                              │  + Ollama (local)│
│  @intel      │                              │  + 400+nodes     │
│  @ops        │                              │                  │
│  @comms      │                              │  Backed by:      │
│  @sentinel   │                              │  PostgreSQL 16   │
└──────────────┘                              │  + Runners       │
                                              └──────────────────┘
```

## How Our Agents Use It

### 🔄 Asynchronous Pipeline (Default)

```
Agent → HTTP POST /webhook/my-workflow → n8n runs in background → agent continues
                                    ↓
              n8n completes → calls OpenClaw webhook or posts to Telegram
```

Best for: daily news, file conversion, research formatting, notifications.

### 🔄 Synchronous Task (Await Result)

```
Agent → HTTP POST /webhook-my-task → n8n runs → returns result immediately
```

Best for: quick lookups, format transforms, API bridges.

### 🔄 Cron (No OpenClaw Required)

```
n8n cron trigger (6:00 AM)
  → Fetch RSS feeds
  → Ollama summarizes
  → Write to daily_news.md
  → Telegram: "今日新闻已生成"
```

---

## Pre-Built Workflow Templates

From [n8n.io/workflows](https://n8n.io/workflows) — adapt for our stack:

| Workflow | Nodes | Purpose |
|----------|-------|---------|
| **Daily RSS → AI Summary → Telegram** | RSS, Ollama, Telegram | Daily news automation |
| **PDF Upload → Convert → Notify** | Webhook, PDF tool, Telegram | File pipeline |
| **Research → Notion → Slack** | Tavily/Perplexity, Notion, Slack | Knowledge base |
| **Image Upload → OCR → Extract** | Webhook, OCR node, File | Screenshot reading |
| **Multi-API Monitor → Alert** | HTTP, Filter, Telegram | Service health |

---

## Connecting to Our Stack

| Service | n8n Node | How |
|---------|----------|-----|
| **Ollama (qwen3.5)** | Ollama Chat Model | `host.docker.internal:11434` |
| **Telegram** | Telegram node | Use existing bot token |
| **D: drive** | Read/Write Files from `/data/inbox`, `/data/outbox` | Mounted from Docker |
| **OpenClaw** | Webhook node (receive) + HTTP node (send) | Direct via port 5678 |
| **Email** | IMAP / SMTP node | For email triggers |

---

## First-Time Flow

```
1. docker compose up -d          ← Start n8n
2. Open http://localhost:5678    ← Create admin account
3. Create webhook workflow       ← "When receiving webhook call"
4. Test: curl -X POST localhost:5678/webhook/my-workflow
5. Wire into OpenClaw agent      ← sessions_send triggers POST
```

## Health and Recovery

- Compose mounts `n8n/initdb/` into PostgreSQL as a read-only init directory.
  Avoid single-file init bind mounts; Docker Desktop WSL bind cache can turn a
  stale file mount into a file/directory mismatch and prevent PostgreSQL from
  starting.
- PostgreSQL must be `healthy` before n8n starts.
- n8n exposes `GET /healthz`; Docker checks this endpoint before starting the
  external runner.
- Verify after repair:

```
docker compose -f n8n/docker-compose.yml ps
curl -fsS http://127.0.0.1:5678/healthz
```

## Promotion Gate

Before temporary activation, production promotion, or a live webhook POST test,
run the local promotion validator against the exact saved workflow JSON:

```
python3 tools/n8n_promotion_validator.py \
  --workflow n8n/workflows/pentagon-job-command-center-draft.json \
  --check-db \
  --workflow-id PentagonJobCommandCenterDraft
```

The gate is read-only. It blocks promotion when a Webhook node is missing a
stable top-level `webhookId`, when a workflow path is saved with a
`webhook/` or `webhook-test/` prefix, when duplicate webhook IDs or routes are
present in the same workflow, when the saved draft is already active, or when
stale `webhook_entity` rows exist for the draft workflow before promotion.

## Security

- n8n runs on `localhost:5678` only (Docker maps to 127.0.0.1 by default)
- Credentials are encrypted with `N8N_ENCRYPTION_KEY`
- Webhook endpoints can be password-protected
- Ollama stays on localhost — no API key needed
- All data stays in WSL2 — no cloud egress
