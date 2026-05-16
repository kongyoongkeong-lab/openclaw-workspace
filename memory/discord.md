
# 🎮 Discord Configuration Guide (Corrected)

**Pentagon Team** | **Intel Division**  
**Vault Location:** `memory/discord.md`  
**Last Updated:** 2026-05-14 22:28 GMT+8  
**Classification:** `production`

---

## 📋 Table of Contents

1. [Webhook Architecture](#1-discord-webhook-architecture)
2. [Correct Endpoint Usage](#2-correct-endpoint-usage)
3. [Security & Token Management](#3-security---token-management)
4. [Development Phases](#4-development-phases)
5. [Heartbeat & Observability](#5-heartbeat---observability)

---

## 1. Discord Webhook Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Discord Runtime Stack                                       │
├────────────────────────────────────────────────────────────┤
│  Bot Runtime (discord.py)  │  Incoming Webhooks (CI)        │
│  Two-Way Interaction       │  External → Discord            │
└────────────────────────────────────────────────────────────┘
```

**Key Distinctions:**

| Type | Purpose | Direction | Recommended |
|------|---------|-----------|-------------|
| **Bot Runtime** | Command API, event dispatch | Bidirectional | `discord.py` |
| **Incoming Webhook** | CI alerts, notifications | External → Discord | GitHub Actions, DataDog |
| **Outgoing Webhook** | Local server → Discord | Discord → External | 后期实现 |
| **Slash Commands** | Bot command API | Bot → User | 后期实现 |
| **Gateway Events** | Agent runtime | Discord → Bot | Phase 3 |

---

## 2. Correct Endpoint Usage

### 📡 Incoming Webhook Setup

**UI Path:**
```
Server Settings → Integrations → Webhooks → Add Webhook
```

**API Flow:**
```
POST /api/webhooks  →  Create webhook
GET  /api/webhooks/{id}  →  Fetch webhook
POST https://discord.com/api/webhooks/{id}/{token}  →  Send message
```

**Correct Payload Endpoint:**
```text
POST https://discord.com/api/webhooks/{webhook_id}/{token}
```

**NOT:**
```text
❌ POST /api/channels/{channel_id}/webhooks  (creates webhook, not sends message)
```

### 📝 Usage Examples

**GitHub Commit Notification:**
```bash
curl -X POST "https://discord.com/api/webhooks/WEBHOOK_ID/TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "📦 Commit pushed to main",
    "username": "GitHub Actions",
    "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
  }'
```

---

## 3. Security & Token Management

### 🔐 Token Rotation Strategy

**❌ WRONG:** `Rotate Bot Token every 24h`

| Token Type | Rotation Policy | Rationale |
|------------|-----------------|-----------|
| **Bot Token** | Long-term, rotate only on leak | 避免 runtime 断线、CI 不匹配、webhook 失效 |
| **Webhook URL** | Single-use, discard on leak | 一次性凭证，泄漏即废弃 |
| **GitHub Secrets** | 90 days (平台最佳实践) | CI 系统要求 |
| **Local `.env`** | Never commit to Git | 本地加密存储，使用 `git-secrets` 或类似工具 |

### 🛡️ Best Practices

```bash
# Store tokens in environment variables
export DISCORD_BOT_TOKEN="${DISCORD_BOT_TOKEN}"
export DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL}"

# Never log tokens
# Never commit .env to Git
# Use .gitignore for credentials
```

---

## 4. Development Phases

### 🎯 Phase 1（当前）: Discord Bot Runtime

**Goal:** 验证 runtime 稳定运行 30~60 分钟

**Tasks:**
- ✅ `!ping` command
- ✅ Message dispatch
- ✅ Event loop stability
- ✅ Reconnect behavior
- ✅ Logging
- ⏸️ Slash commands (defer to Phase 2)
- ⏸️ Webhook relays (defer to Phase 2)
- ⏸️ Outgoing integrations (defer to Phase 3)

**Validation:**
- 观察是否断线
- 观察 heartbeat warning
- 观察 reconnect behavior
- 观察 event loop lag
- 观察 memory leak

---

### 🎯 Phase 2（稳定后）: CI → Discord Webhook

**Goal:** 低风险高价值的通知管道

**Example:**
```
GitHub Action
  → CI fail
  → Discord alert via webhook
```

---

### 🎯 Phase 3（以后）: Discord as Runtime Control Plane

**Goal:** 真正的 agent runtime

**Commands:**
- `!ops restart`
- `!news`
- `!snapshot`
- `!trace`

---

## 5. Runtime Stability Checklist (Phase 1 Exit Criteria)

**Phase 1 Exit Criteria:**

- [ ] `!ping` stable
- [ ] reconnect verified (断网 30 秒)
- [ ] heartbeat stable > 1h
- [ ] no memory growth
- [ ] latency < 500ms
- [ ] event loop no stall
- [ ] graceful shutdown works

---

## 6. Heartbeat & Observability (Contract-First)

### 📊 Heartbeat Metrics Schema

**Old:** `print("[HEARTBEAT] Runtime alive")` ❌ human-readable only

**Upgrade To:**
```python
runtime_metrics = {
    "heartbeat_delta": delta,
    "guild_count": len(client.guilds),
    "latency_ms": round(client.latency * 1000, 2),
    "event_loop_state": "healthy"
}
```

### ⚠️ Why `print()` is Not Enough

Discord runtime 最早坏掉的地方，通常不是 `bot offline` 而是：

- latency 飙升
- gateway reconnect loop
- event loop starvation
- websocket heartbeat jitter

**Bot 看起来在线，但其实已经"半死"**。

### 🔧 Contract-First Philosophy

```text
documentation ≠ truth source
contract = truth source
```

See `runtime/contracts/` for official constraints:

- `discord_runtime_contract.json` - Required intents, permissions
- `heartbeat_contract.json` - Latency, jitter thresholds
- `webhook_contract.json` - Token rotation policies

**CI 才能检查：**

- required intents
- required permissions
- required heartbeat interval
- runtime expectations

---

## 🚀 Pentagon Status

**Endpoint:** ✅ Corrected  
**Token Rotation:** ✅ Best practices applied  
**Development Path:** ✅ 3-phase roadmap defined  
**Heartbeat:** ✅ Observability template ready  
**Contracts:** ✅ `runtime/contracts/` deployed  

**NO_REPLY**
