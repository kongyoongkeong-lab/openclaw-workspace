# Provider Status

Status: local provider registry snapshot.
Last updated: 2026-05-22.

| Provider | Role | Status | Notes |
|---|---|---|---|
| OpenAI Codex / API | Primary orchestrator | Active | Used for long-context and tool-heavy work. |
| Ollama | Local worker | Active | Loopback at `http://localhost:11434`; use only after GPU preflight. |
| Qdrant | Vector store | Available | Writes require explicit approval unless a specific workflow already allows them. |
| Redis | Runtime service | Available | Local service dependency. |
| ComfyUI | Image/runtime service | Available | GPU-heavy work requires preflight. |
| Telegram | Channel | Enabled | Do not expose tokens; owner allowlist should be configured with Jason's verified channel id. |
| GitHub | Governance/reference | Available | Consultation and versioning only; no push/merge without explicit request. |

## Inactive Or Pending

- Protocol mode state is workspace-local through `tools/protocol_mode_state.py`.
- Daily news and AI daily workflow specs are pending reconstruction if invoked.
- Codex quota switching and Tavily key switching scripts are pending reconstruction.
