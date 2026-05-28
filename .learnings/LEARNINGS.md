# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260525-001] best_practice

**Logged**: 2026-05-25T03:20:00+08:00
**Priority**: medium
**Status**: pending
**Area**: automation

### Summary
Use `python3` in this WSL workspace; `python` may not exist on PATH.

### Details
Validation commands for the new `automation-protocol` skill failed when invoked as `python ...` because `/bin/bash` reported `python: command not found`. The same commands passed with `python3`.

### Suggested Action
Prefer `python3` in workspace scripts, docs, validation commands, shortcut registry entries, and quick checks.

### Metadata
- Source: error
- Related Files: `skills/automation-protocol/SKILL.md`, `shortcuts.md`
- Tags: wsl, python, validation
