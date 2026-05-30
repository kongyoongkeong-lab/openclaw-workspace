# Security Policy

## Reporting Security Issues

Do not open public GitHub issues for secrets, credentials, account access, token exposure, or exploitable automation behavior.

Report security concerns directly to the repository owner through the agreed private channel.

## Sensitive Data Rules

- Never commit API keys, OAuth tokens, Telegram bot tokens, browser cookies, `.env` files, credential exports, or generated auth files.
- Keep local runtime state, caches, logs with personal data, and machine-specific credentials out of Git.
- Rotate any credential that may have been committed, pasted, logged, or uploaded.
- Prefer reviewed markdown summaries over raw logs when durable memory needs to be kept.

## Supported Scope

Security review applies to tracked repository content, CI workflows, memory governance files, and automation scripts. Local machine configuration and external service account settings remain owner-managed unless explicitly documented.
