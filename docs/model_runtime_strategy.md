# OpenClaw Hybrid Model Runtime Strategy

Status: active baseline
Owner: Jason / Pentagon `@main`
Date: 2026-05-22

## Goal

Run OpenClaw as a hybrid model system:

- API model handles orchestration, long context, tool-heavy workflows, current external knowledge, and high-stakes synthesis.
- Local Ollama models handle compact private reasoning, routing, summarization, embeddings, and low-risk worker tasks.
- Context is managed as a budgeted resource. Long outputs must be summarized into artifacts instead of accumulating in chat.
- If API models are unavailable, the system degrades to local Ollama mode for compact reasoning and local file work.
- GitHub stores reviewed configuration and docs only. It is not the source of runtime truth and should not be restored blindly from old backups.

## Hardware Baseline

Observed GPU:

- GPU: NVIDIA GeForce RTX 4070 SUPER
- VRAM: 12,282 MiB observed
- Effective local-inference ceiling: 9,728 MiB
- Target active utilization: 70-85%

The 9.5 GiB ceiling leaves headroom for WSL2, display/driver overhead, Ollama overhead, and concurrent tooling. Temporary bursts are acceptable only when monitored.

## Installed Local Models

Current Ollama inventory:

- `qwen3.5:9b` as primary local reasoning model
- `qwen3.5:4b` as faster local worker
- `qwen3.5:2b` as tiny fallback/router
- `llava:latest` and `llava:7b-v1.5-q4_K_S` for local vision tasks
- `nomic-embed-text:latest` for local embeddings

## Routing Modes

### Hybrid

Default production mode.

Use API for:

- Multi-step orchestration
- Long context
- Codebase-wide edits
- Complex debugging
- Internet-current decisions
- Final synthesis across agents

Use Ollama for:

- Private compact reasoning
- Local classification/routing
- Short summarization
- Embeddings
- GPU-worker tasks when VRAM is safe

### API

Use when reliability, context length, current docs, or tool orchestration matter more than local execution.

Local models remain fallback for private low-risk tasks.

### Local

Use when privacy, low cost, and local control matter more than peak capability.

API remains fallback for long-context or high-complexity work.

## Context Window Protection

Previous context overflow is treated as a design failure, not as an acceptable runtime condition.

Live context should contain only:

- Current user intent
- Active plan
- Current blockers
- Short summaries of relevant state
- File paths and commit ids needed for continuation

Long or stable content must move into artifacts:

- Architecture decisions: `memory/decisions/`
- Stable rules: `memory/system/`
- User preferences: `memory/preferences/`
- Longer strategy or implementation notes: `docs/`
- Runtime logs and daily notes: `memory/YYYY-MM-DD.md` or future `memory/logs/`

Budget rules:

- At 50% estimated context pressure, summarize and offload before continuing.
- At 65%, keep only current-step context and reload exact files from disk.
- At 80%, stop expansion, write a handoff summary, and resume from artifacts.

Tool output rules:

- Do not paste large command outputs into future prompts.
- Summarize high-signal lines and keep full output on disk only when needed.
- Prefer `rg`, targeted file reads, and exact file references over broad dumps.

## API Failure and Local Fallback

When API models are unavailable:

1. Switch active routing to local behavior for compact tasks.
2. Use `qwen3.5:9b` when VRAM is safe.
3. Use `qwen3.5:4b` when other GPU work is active.
4. Use `qwen3.5:2b` for small classification, routing, and short summaries.
5. Avoid claims that require current internet knowledge unless search tools are working.
6. Split large work into file artifacts, then process one artifact at a time.

When local models are unavailable:

1. Continue API-first if API quota and network are available.
2. Skip private local summarization and embeddings until Ollama/GPU recovers.
3. Keep degraded-mode decisions visible in `memory/decisions/` if they affect architecture.

## Local Model Preflight

Before local LLM or image-generation work:

1. Check GPU memory with `/home/jason/check_gpu.sh` when available.
2. Confirm projected VRAM use stays below 9,728 MiB.
3. Prefer `qwen3.5:4b` or `qwen3.5:2b` if other GPU jobs are active.
4. Use `qwen3.5:9b` only when it fits comfortably.
5. Do not start persistent GPU workers without explicit approval.

## GitHub Policy

The remote `kongyoongkeong-lab/openclaw-workspace` contains older backup material. The optimized setup should:

- Keep local files as source of truth.
- Avoid pulling old backup files into the live workspace.
- Commit only reviewed docs, config, and safe scripts.
- Keep runtime state, memory logs, tokens, generated files, and bulky backups out of git.
- Run secret scan before the first push.

## Operational Commands

Set mode:

```bash
python3 /home/jason2ykk/.openclaw/workspace/tools/model_mode_state.py set hybrid --source manual
python3 /home/jason2ykk/.openclaw/workspace/tools/model_mode_state.py set api --source manual
python3 /home/jason2ykk/.openclaw/workspace/tools/model_mode_state.py set local --source manual
```

Show mode:

```bash
python3 /home/jason2ykk/.openclaw/workspace/tools/model_mode_state.py get
```

Show runtime status:

```bash
python3 /home/jason2ykk/.openclaw/workspace/tools/model_runtime_status.py
```

Show routing decision:

```bash
python3 /home/jason2ykk/.openclaw/workspace/tools/model_route_decision.py --task-type synthesis
python3 /home/jason2ykk/.openclaw/workspace/tools/model_route_decision.py --task-type private --no-api-available
python3 /home/jason2ykk/.openclaw/workspace/tools/model_route_decision.py --task-type long-context --context-ratio 0.55
```
