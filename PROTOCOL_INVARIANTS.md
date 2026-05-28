# OpenClaw Protocol Invariants

Status: local hybrid runtime source of truth.
Last updated: 2026-05-22.

## Runtime Boundary

- This workspace is a personal trusted-operator OpenClaw runtime for Jason.
- Broad filesystem and execution tools are allowed only inside that trust boundary.
- Before adding untrusted users, public channels, shared agents, or remote exposure, enable sandboxing and workspace-only filesystem restrictions or split the runtime into a separate gateway/OS boundary.

## Secrets

- Do not print, store in reports, commit, or broadcast API keys, access tokens, refresh tokens, Telegram bot tokens, gateway tokens, passwords, or raw credential files.
- Supported runtime secrets should use OpenClaw SecretRefs.
- Secret-bearing backups require explicit confirmation before execution.

## Hardware

- GPU: NVIDIA GeForce RTX 4070 SUPER.
- Observed VRAM: 12282 MiB.
- Local inference hard ceiling: 9728 MiB used VRAM.
- Target sustained active utilization: 70-85%.
- Burst utilization up to 95% is allowed only when actively monitored.
- Run `tools/check_gpu.sh` before local LLM or image-generation work.

## Model Routing

- Default mode is hybrid.
- API handles orchestration, long context, tool-heavy work, codebase-wide changes, current external knowledge, and final synthesis.
- Ollama handles compact/private reasoning, local summarization, classification, embeddings, and low-risk vision when GPU preflight passes.
- API-first, local-first, and hybrid model preferences are workspace-local state unless Jason explicitly requests OpenClaw global runtime config changes.

## Protocol Modes

- Protocol mode is workspace-local state managed by `tools/protocol_mode_state.py`.
- `stable` is the default operating mode.
- `architect_mode` allows architecture analysis and planning, but it does not waive safety invariants.
- Production activation, new agents, telemetry expansion, Qdrant writes, workflow changes, and persistent background tasks require explicit approval in every protocol mode.

## GitHub

- GitHub is a reviewed history and consultation source, not an automatic restore source.
- Do not blindly merge or restore old backup content.
- Do not push secrets, raw memory logs, runtime state, generated media, or bulky local artifacts.
- Remote protocol files can be cherry-picked structurally only after rewriting them for this local hybrid runtime.
