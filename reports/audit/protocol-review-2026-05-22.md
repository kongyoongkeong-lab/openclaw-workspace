# Protocol Review — 2026-05-22

## Scope
Reviewed protocol/config surface in `openclaw-workspace`:

- Root protocols: `*_PROTOCOL.md`, `WORKFLOW_PROTOCOL.md`, `COMMS_PROTOCOL.md`
- Agent specs: `AGENTS.md`, `TOOLS.md`, `AGENT_CONFIG.json`, sub-agent files
- Memory/search workflows: `memory/LTM_PROTOCOL.md`, `intel/SEARCH_PROTOCOL.md`
- Runtime workflows: `workflows/daily_news.md`, `workflows/daily_ai.md`, `workflows/video/*`
- GitHub Actions: `.github/workflows/*.yml`

## Current Strengths

1. **Good protocol coverage** — workflow, LTM, access control, compliance, disaster recovery, upgrade, testing/rollback, session lifecycle, SLA, webhook, media, PDF, RSS/Notion are all represented.
2. **GitHub cold-storage model is solid** — workspace commits, backup tags, issues, audit reports, and CI hooks give traceability and rollback.
3. **Daily workflows are mature** — `daily_news.md` and `daily_ai.md` include cache policy, validation gate, source scoring, output templates, fallback rules, and safety rules.
4. **Cloud-native direction is mostly enforced** — active config uses DeepSeek/OpenAI/Google APIs; stale local model references are mostly historical docs, not active config.
5. **Security awareness exists** — token/PAT leakage rules, secret scan workflow, access-control protocol, and sentinel role are documented.

## Findings / Risks

### P0 — Runtime team mismatch

**Finding:** `agents_list` currently exposes only `main` as spawn-allowed, while protocols describe a Pentagon team with `@intel`, `@ops`, `@comms`, and `@sentinel`.

**Impact:** The documented team exists as protocol/design, but runtime delegation is not fully enabled. This can confuse users and reduce orchestration reliability.

**Fix:** Align gateway/session allowlist with `AGENT_CONFIG.json`, or explicitly mark the sub-agents as logical roles until spawn permissions are enabled.

---

### P1 — Stale local-model references remain in historical/non-active docs

**Observed references:**

- `HEARTBEAT.md` notes GPU/local inference scrub action; acceptable as history.
- `WORKFLOW_PROTOCOL.md` says compaction model is DeepSeek, not Ollama; acceptable but grep-triggering.
- Older reports/memory files still mention `qwen3.5` / `ollama` as historical context.

**Impact:** Automated audits may flag false positives; future agents may misread stale historical docs as current posture.

**Fix:** Add a top-level `CURRENT_RUNTIME.md` or `RUNTIME_BASELINE.md` declaring active posture, and tag historical files with `Historical / Do Not Use For Current Routing`.

---

### P1 — Cross-protocol invariants are duplicated but not centrally enforced

**Examples:** cloud-native-only, GitHub PAT secrecy, approval before external writes, cache-first news behavior, no local LLM routing.

**Impact:** Drift risk. One protocol may be updated while another remains stale.

**Fix:** Add `PROTOCOL_INVARIANTS.md` and make each protocol reference it instead of restating core rules.

---

### P1 — External-write safeguards are unevenly explicit

**Protocols involving external writes:** GitHub Issues, Notion, webhook receiver, Slack/Telegram delivery, PDF/report commit, media generation workflows.

**Impact:** Some files rely on global tool policy rather than local protocol text. Future agents reading only one protocol may miss approval/idempotency/rate-limit requirements.

**Fix:** Add a standard section to every external-write protocol:

```md
## External Write Guardrails
- Confirm user intent for irreversible/external writes unless explicitly requested.
- Use dry-run where available.
- Ensure idempotency key or dedupe marker.
- Respect 429 / Retry-After.
- Record result in audit log.
- Provide rollback path when possible.
```

---

### P2 — GitHub Actions coverage is basic

Current workflows exist for markdown lint, secret scan, benchmark, webhook test. Missing/weak areas:

- Protocol schema consistency check
- Link checker for docs
- Agent registry/config consistency check
- Workflow file validation for large Comfy/video JSON templates
- Automatic issue creation on failed scheduled health checks

**Fix:** Add `protocol-audit.yml` running:

- JSON/YAML syntax validation
- grep for active forbidden model references
- required-section check for protocol files
- agent registry vs runtime allowlist report
- markdown link check

---

### P2 — Media protocols reference Comfy/workflow templates while actual configured API is Google Veo

**Finding:** `VIDEO_PROTOCOL.md` and `PHOTO_PROTOCOL.md` emphasize workflow templates/Comfy-style files, but current `video_generate list` shows only Google configured for video.

**Impact:** User-facing capability explanation can drift from actual provider state.

**Fix:** Add `PROVIDER_STATUS.md` generated from `image_generate list` / `video_generate list`, or add a provider-state section to media protocols.

---

### P2 — LTM depends on embeddings but failure mode needs stronger fallback

**Finding:** `memory_search` currently fails due to Gemini embedding quota cap. Manual file/git fallback works, but protocol should codify this.

**Impact:** Questions about prior work can degrade if semantic memory is unavailable.

**Fix:** Update `LTM_PROTOCOL.md` with fallback order:

1. `memory_search`
2. direct `memory/YYYY-MM-DD.md`, `STATUS.md`, `vault.md`
3. `git log --since/--grep`
4. session history
5. web/GitHub only if local evidence insufficient

---

## Recommended Improvement Plan

### Phase 1 — Consistency hardening

- Create `PROTOCOL_INVARIANTS.md`.
- Create `CURRENT_RUNTIME.md`.
- Add `External Write Guardrails` boilerplate to protocols with external side effects.
- Update `LTM_PROTOCOL.md` memory fallback behavior.

### Phase 2 — CI audit

- Add `.github/workflows/protocol-audit.yml`.
- Add `scripts/protocol_audit.py`.
- Fail CI only on active-config violations; warn on historical files.

### Phase 3 — Runtime/team alignment

- Decide whether `@intel/@ops/@comms/@sentinel` should be real spawnable agents or documented logical roles.
- If real: update gateway/session allowlist and verify with `agents_list`.
- If logical: update `AGENTS.md` and `WORKFLOW_PROTOCOL.md` wording to prevent overclaiming.

### Phase 4 — Provider state synchronization

- Generate `PROVIDER_STATUS.md` from model-provider list tools.
- Update media protocols to state: configured provider vs available-but-not-configured providers.

## Immediate Next Actions

1. Open GitHub issue with this audit summary.
2. Add the audit report to repo history.
3. Implement Phase 1 patches in a separate PR/commit after owner approval.

## Verification Performed

- Listed protocol/config files with `find`.
- Validated JSON syntax for `AGENT_CONFIG.json` and `access_control.json`.
- Validated GitHub Actions YAML parse.
- Grepped for stale local model references.
- Checked `gh auth status` and active repository.
- Confirmed current runtime spawn allowlist shows only `main`.
