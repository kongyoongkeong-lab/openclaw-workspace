# 📡 Channel Protocol — v2

**Owner:** @comms (Communication Agent)
**Scope:** Multi-channel delivery, Telegram pairing, GitHub status
**Updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Channel Architecture

```
@main (source)
  │
  ▼
┌──────────┐
│  @comms   │ → Format → Route → Deliver
└─────┬────┘
      │
      ├── ✅ Webchat (OpenClaw Control UI)
      │    Direct session, real-time, full Markdown
      │
      ├── 📱 Telegram
      │    Push notifications, pair-mode, async delivery
      │
      ├── 🔧 Slack (configurable)
      │    Log streaming, weekly reports, alerts
      │
      └── 🐙 GitHub Issues
           Incident reports, SLA summaries, audit logs
```

## Active Channels

| Channel | Status | Mode | Latency | Format |
|---------|--------|------|---------|--------|
| **Webchat** | ✅ Active | Interactive | Real-time | Full Markdown |
| **Telegram** | ✅ Enabled | Push (pair-mode) | < 5s | Markdown + media |
| **Slack** | ⚙️ Configurable | Webhook | < 10s | JSON payload |
| **GitHub Issues** | ✅ Active | Incident logging | On demand | Markdown |

## Telegram Protocol

### Pairing Mode

```json
{
  "version": 1,
  "requests": [],
  "allowFrom": []
}
```

Only paired Telegram IDs can trigger @ops commands via Telegram. Pairing flow:

```bash
# User sends /pair to bot
# Bot responds with pairing code
# User confirms via webchat or reply
# ID added to telegram-pairing.json allowFrom list
```

### Message Format

| Type | Format | Example |
|------|--------|---------|
| Alert | `🚨 **{title}**` | `🚨 **ComfyUI Down**` |
| Daily Pulse | `📊 **Pentagon Pulse**` | `📊 **Pentagon Daily Pulse**` |
| Task Complete | `✅ **{agent}**: {summary}` | `✅ **@ops**: Deployed update` |
| Status | `🟢 **Stable** / 🟡 **Warning** / 🔴 **Critical**` | Status indicator |

### Telegram Commands

| Command | Action | Scope |
|---------|--------|-------|
| `/status` | Query system health | All users |
| `/pair` | Initiate pairing | First-time users |
| `/report` | Request daily pulse | Paired users only |
| `/recover` | Trigger recover_all.sh | Owner only |

## Webchat (Control UI) Protocol

### Message Routing

```
User → OpenClaw Control UI → @main → @comms (if needed) → Response
```

### Format Support
- **Full Markdown:** Headers, lists, code blocks, tables, bold, italic
- **LaTeX Math:** `$$ E = mc^2 $$`
- **Code:** Triple-backtick with language tags
- **Media:** Image/audio/video attachments via `MEDIA:`
- **Embeds:** Canvas-rich embeds `[embed ref="..." /]`

## Slack Protocol (Configurable)

When enabled, Slack receives:

```json
{
  "channel": "#pentagon-logs",
  "attachments": [
    {
      "color": "#36a64f",
      "title": "✅ Service Health — OK",
      "fields": [
        {"title": "Gateway", "value": "Active", "short": true},
        {"title": "GitHub", "value": "Synced", "short": true}
      ],
      "footer": "Pentagon Bot",
      "ts": 1234567890
    }
  ]
}
```

## GitHub Integration

### What Gets Pushed Where

| Content | Channel | Trigger |
|---------|---------|---------|
| Incident report | GitHub Issue | Auto-recovery fails ×2 |
| SLA report | GitHub Issue | Monthly |
| Audit report | Git commit → `reports/audit/` | Weekly |
| Daily pulse | Telegram + Webchat | Daily cron |

### GitHub Issue as Channel

```bash
# Push a notification to GitHub Issues
gh issue create \
  --repo kongyoongkeong-lab/openclaw-workspace \
  --title "[comms] ${subject}" \
  --label "notification" \
  --body "${message_body}"
```

### Channel Health Check

```bash
#!/bin/bash
# channel_health.sh — verify all channels are operational

echo "🔍 Channel Health Check — $(date)"

# Webchat: always up (direct session)
echo "  ✅ Webchat (direct session)"

# Telegram: check bot connectivity
if curl -s "https://api.telegram.org/bot$(cat ~/.openclaw/credentials/telegram-* 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin).get("token",""))')/getMe" 2>/dev/null | grep -q ok; then
  echo "  ✅ Telegram (bot responsive)"
else
  echo "  ❌ Telegram (bot check failed)"
fi

# GitHub: check API
if gh api repos/kongyoongkeong-lab/openclaw-workspace 2>/dev/null | grep -q full_name; then
  echo "  ✅ GitHub Issues (API responsive)"
else
  echo "  ❌ GitHub Issues (API failed)"
fi
```

## Template Reference

### Daily Pulse

```markdown
📊 **Pentagon Daily Pulse** — {date}

**Services:**
- Gateway: ✅ | Qdrant: ✅ | Redis: ✅ | ComfyUI: ✅

**GitHub:**
- Workspace: {commits} commits, {issues} open issues
- Config: {config_commits} commits
- Last backup: {backup_tag}

**Health:** 🟢 Stable
```

### Alert

```markdown
🚨 **Pentagon Alert** — {severity}

- **Agent:** {agent_id}
- **Issue:** {description}
- **Auto-recovery:** {attempts}
- **Status:** ✅ Fixed / ❌ Escalated
```

### Task Complete

```markdown
✅ **{agent}** — {task}

**Summary:**
{result}

**Latency:** {time}
🔗 {link_if_any}
```

## Channel Configuration Storage

```json
{
  "comms": {
    "telegram": {
      "enabled": true,
      "pairing_required": true,
      "allow_from": []
    },
    "slack": {
      "enabled": false,
      "webhook_url": null
    },
    "webchat": {
      "enabled": true
    },
    "github_issues": {
      "enabled": true,
      "incident_repo": "kongyoongkeong-lab/openclaw-workspace"
    }
  }
}
```


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.

## Files

| File | Purpose |
|------|---------|
| `CHANNEL_PROTOCOL.md` | This document |
| `comms/AGENTS.md` | Comms agent role definition |
| `comms/TOOLS.md` | Channel tool reference |
| `comms/USER.md` | Delivery preferences |
| `comms/BOOTSTRAP.md` | Startup directives |
| `~/.openclaw/credentials/telegram-*.json` | Telegram pairing + tokens |
| `channel_health.sh` | Channel verification script |
