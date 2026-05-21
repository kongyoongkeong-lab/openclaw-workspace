# 🔌 Plugin & Skill Hot-Reload Protocol — v1

**Owner:** @main (Orchestrator)
**Scope:** Dynamic skill loading, plugin lifecycle, version management
**Updated:** 2026-05-22

## Skill Lifecycle

```
     ┌─────────┐
     │  Idle   │ ← skills/ directory
     └────┬────┘
          │ LOAD
          ▼
     ┌─────────┐
     │ Active  │ ← Register with agent, ready to use
     └────┬────┘
          │ UNLOAD / RELOAD
          ▼
     ┌─────────┐
     │ Removed │ ← Unregistered, directory preserved
     └─────────┘
```

## Skill Directory Structure

```
skills/
├── README.md
├── SKILL.md                    # Skill registration manifest
├── image-ocr-1.0.0/            # Installed skill (versioned)
├── antigravity-image-gen-2.0.0/
└── symlinks/                   # Optional: symlinks to agents
    ├── intel → ../image-ocr-1.0.0
    └── ops   → ../antigravity-image-gen-2.0.0
```

## SKILL.md Format

```markdown
---
name: image-ocr
version: 1.0.0
description: Extract text from images using OCR
license: MIT
agent: intel
tags: [ocr, image, text]
dependencies: [pytesseract, pillow]
---

# Image OCR Skill

Extracts text from uploaded images using Tesseract OCR.

## Usage
Process an image and return extracted text.
```

## Load/Reload Workflow

```bash
# 1. Add skill to directory
mkdir -p skills/my-skill-1.0.0
cp SKILL.md skills/my-skill-1.0.0/

# 2. Register in agent config (if required)
# Edit AGENT_REGISTRY.json to add capability

# 3. Commit to GitHub
git add skills/my-skill-1.0.0/
git commit -m "skill: add my-skill v1.0.0"
git push origin master

# 4. Reload (if hot-reload supported)
# System detects new skill in skills/ and registers on next heartbeat
```

## GitHub Integration

```bash
# List available skills from GitHub
gh search code "SKILL.md" --repo=kongyoongkeong-lab/openclaw-workspace \
  -- --match "**/skills/*/SKILL.md"

# Track skill versions via git tags
git tag skill-image-ocr-1.0.0
git tag skill-antigravity-image-gen-2.0.0
git push origin --tags
```

## Version Management

```bash
# Rollback a skill
git checkout skill-image-ocr-1.0.0~1 -- skills/image-ocr-1.0.0/
git commit -m "rollback: image-ocr skill to previous version"
```

## Current Skills Inventory

| Skill | Version | Agent | Status |
|-------|---------|-------|--------|
| `image-ocr` | 1.0.0 | @intel | ✅ Installed |
| `antigravity-image-gen` | 2.0.0 | @ops | ✅ Installed |

## Files

| File | Purpose |
|------|---------|
| `SKILL_HOT_RELOAD_PROTOCOL.md` | This document |
| `skills/` | Skill storage (git-tracked) |
| `AGENT_REGISTRY.json` | Capability registration |
