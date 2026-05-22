# Protocol Invariants — v1

**Owner:** @main + @sentinel  
**Status:** Active  
**Updated:** 2026-05-22

These rules override individual protocol wording when protocol files drift.

## Runtime Posture

- Cloud-native inference only.
- Do not route tasks to local Ollama/local GPU/local LLM endpoints.
- Current active model/provider state must be checked from runtime tools or `CURRENT_RUNTIME.md`, not historical reports.

## Security

- Never expose Telegram bot tokens, Tavily keys, GitHub PATs, Notion tokens, provider API keys, or webhook secrets.
- Credentials stay outside git under `~/.openclaw/credentials/`, provider-specific config stores, or GitHub secrets.
- Any file generated from external documents must be scanned for secrets/PII before commit.

## External Write Guardrails

For irreversible or external side-effect actions, including GitHub writes, Notion sync writes, webhook creation, Telegram/Slack sends, provider media generation, remote config changes, and public issue/PR creation:

1. Confirm user intent unless the user explicitly requested the action.
2. Prefer dry-run or preview when available.
3. Use idempotency/dedupe markers when a repeated action could duplicate state.
4. Respect `429` and `Retry-After`; do not tight-loop retries.
5. Record durable result in git, issue comment, report, or memory file when relevant.
6. Provide rollback path or named blocker when rollback is impossible.

## GitHub Use

- Use `gh` CLI for repo operations when available.
- Commit only intentional artifacts; avoid staging runtime caches unless explicitly part of the task.
- Do not commit credentials, raw private chats, or provider output with hidden PII.

## Memory Fallback

If semantic memory search is unavailable, use direct memory files, `git log`, and session history before claiming no memory exists.

## User-Facing Accuracy

- Distinguish configured runtime capability from documented/available-but-unconfigured provider support.
- If `agents_list` exposes only `main`, describe sub-agents as protocol roles unless runtime allowlist is updated.
