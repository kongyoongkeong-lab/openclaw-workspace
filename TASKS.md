# Pentagon Task Board

**States:** `Inbox` → `Assigned` → `In Progress` → `Review` → `Done` | `Failed`

| ID | Description | State | Agent | Artifact | Created | Done |
|----|------------|-------|-------|----------|---------|------|
| T-089 | Add Shortcut Governance Phase 1 | Done | @main | `tools/shortcut_doctor.py`; `tools/shortcut_status.py`; `tools/pending_action.py`; `config/shortcut_manifest.json`; `data/shortcut_usage/shortcut_usage.jsonl` | 2026-06-16 | 2026-06-16 |
| T-004 | Create reusable automation protocol skill and shortcut routing | Done | @main | `skills/automation-protocol/`; `shortcuts.md`; `memory/system/capability_map.md` | 2026-05-25 | 2026-05-25 |
| T-003 | Add safe Hugging Face model download helper | Done | @main | `tools/huggingface_download.py`; `docs/huggingface_setup.md` | 2026-05-25 | 2026-05-25 |
| T-002 | Finalize Hugging Face CLI/token/account preflight | Done | @main | `tools/huggingface_preflight.py`; `docs/huggingface_setup.md` | 2026-05-25 | 2026-05-25 |
| T-001 | Harden `服务检查` into read-only health report command | Done | @main | `tools/system_health_check.py`; `docs/system_health_check.md` | 2026-05-25 | 2026-05-25 |

<!-- Add new tasks above this line -->
<!-- Format: | T-### | Short description | Inbox / Assigned / In Progress / Review / Done / Failed | @agent | /shared/artifacts/T-###/ | YYYY-MM-DD | YYYY-MM-DD | -->

## Active Tasks

*(tasks currently in Inbox, Assigned, In Progress, or Review)*

## Completed This Session

- `[2026-05-25 03:20 +08] [@main] Done: created automation-protocol skill, added file probe helper, registered automation shortcuts, and validated skill frontmatter.`
- `[2026-05-25 02:44 +08] [@main] Done: added Hugging Face safe download planner with model access, disk capacity, target-state checks, and explicit --yes gate.`
- `[2026-05-25 02:29 +08] [@main] Done: verified Hugging Face auth for jason2ykk, patched CLI auth probing for newer hf syntax, and updated HF setup docs/capability state.`
- `[2026-05-25 02:17 +08] [@main] Done: created and verified read-only system health checker; updated shortcut registry, capability map, and stable rules.`

---

## Task Lifecycle Rules

- Orchestrator (@main) owns state transitions
- Every transition gets a comment: `[Agent] Action: details`
- All deliverables go to `/shared/artifacts/` — never to personal workspaces
- Review is mandatory — skip only if @main explicitly documents the override
- `Failed` is a valid end state — capture the reason and move on
