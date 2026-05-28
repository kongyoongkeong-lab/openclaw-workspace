# Failure Journal

Purpose: durable, sanitized failure memory for OpenClaw/Pentagon operations.

Use this directory for recurring or high-signal failures that should change future behavior. Keep transient command noise in daily logs; promote only failures with a reusable prevention rule.

## Files

- `INDEX.md` — active failure registry and routing checklist.
- `TEMPLATE.md` — canonical entry format.
- `YYYY-MM.md` — monthly failure entries.

## Logging Rules

- Never store raw secrets, tokens, cookies, private keys, passwords, or full environment dumps.
- Redact account identifiers unless the account label itself is required for routing.
- Keep command output short. Capture the error class, the attempted operation, the recovery, and the prevention rule.
- Mark `Status` as `open`, `mitigated`, `fixed`, or `watch`.
- Promote broadly applicable prevention rules to `memory/system/stable_rules.md`.
- Link tool/service-specific prevention rules from `memory/system/capability_map.md` when useful.

## Entry ID Format

`ERR-YYYYMMDD-NNN`

Example: `ERR-20260525-001`

## Helper CLI

Use `tools/failure_journal.py` for new entries whenever possible.

```bash
tools/failure_journal.py next-id
tools/failure_journal.py scan
tools/failure_journal.py add \
  --title "Short Failure Title" \
  --area other \
  --summary "One concise sentence." \
  --error-signal "Sanitized symptom." \
  --root-cause "Actual cause." \
  --recovery "What worked." \
  --prevention-rule "Future agents should do this first." \
  --dry-run
```

The helper auto-generates `ERR-YYYYMMDD-NNN`, appends to the monthly log, updates `INDEX.md`, and refuses common secret-like input patterns.
