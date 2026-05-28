# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---
## 🗂️ D: DATA DRIVE (Shared Storage)

All large files live on the Windows D: drive, mounted at `/mnt/d/` in WSL2.

| Folder | WSL Path | Purpose |
|---|---|---|
| `_inbox` | `/mnt/d/_inbox/` | Drag-drop zone — new files for the AI to process |
| `_outbox` | `/mnt/d/_outbox/` | AI-generated results delivered here |
| `archive` | `/mnt/d/archive/` | Completed projects (move from inbox/outbox) |
| `backup` | `/mnt/d/backup/` | OpenClaw system backups |
| `media/input` | `/mnt/d/media/input/` | Raw source media (videos, images, audio) |
| `media/output` | `/mnt/d/media/output/` | Generated media (Wan, Suno, images) |
| `media/archive` | `/mnt/d/media/archive/` | Old media projects |
| `photos` | `/mnt/d/photos/` | Personal photo library |
| `documents` | `/mnt/d/documents/` | PDFs, reports, references |
| `code` | `/mnt/d/code/` | Git repos (read-only copies) |
| `logs` | `/mnt/d/logs/` | Pentagon boot/shutdown logs |
| `temp` | `/mnt/d/temp/` | Scratch space — auto-clean after 7 days |
| `projects` | `/mnt/d/projects/` | Per-project workspace folders |

**Workflow rule:**
- Input → place in `_inbox` or `media/input/{type}`
- Processing → write to `_outbox` or `media/output/{type}`
- Complete → move to `archive\{date}\` or `projects\{name}\`

---
## 📡 INTER-AGENT ROUTING (A2A)
- **Registry First:** Before calling a specialized agent, read `/home/jason2ykk/.openclaw/workspace/agent_registry.json`.
- **Addressing:** Prefer `sessions_send(agentId="sentinel", message="...")` for configured agents. Use a verified `sessionKey` for visible sessions, or `label` as a fallback when the session list confirms it.
- **No Legacy Shape:** Do not use a bare `agent` parameter with `sessions_send`; the loaded OpenClaw tool schema uses `agentId`, `label`, or `sessionKey`.
- **Fallback:** If @sentinel does not respond within 5 seconds, @main assumes Sentinel review duties and reads only the minimum local evidence needed.
