# Current Runtime

Status: active local runtime summary.
Last updated: 2026-05-22.

## OpenClaw

- Runtime: OpenAI Codex through OpenClaw.
- Active default API model: `openai/gpt-5.5` with Codex agent runtime.
- Fallback model: `openai/gpt-5.5`.
- Current observed context window: 1,000,000 tokens.
- Gateway bind: loopback.

## Workspace Model Policy

- Active workspace model mode: hybrid.
- API role: orchestrator and long-context executor.
- Ollama role: local worker for compact/private tasks when GPU preflight passes.
- Local model base URL: `http://localhost:11434`.

## Local Models

- Primary reasoning: `qwen3.5:9b`.
- Fast reasoning: `qwen3.5:4b`.
- Tiny fallback: `qwen3.5:2b`.
- Vision: `llava:latest`.
- Embeddings: `nomic-embed-text:latest`.

## Hardware Guardrail

- GPU: NVIDIA GeForce RTX 4070 SUPER.
- VRAM hard ceiling for local inference: 9728 MiB used.
- GPU preflight command: `tools/check_gpu.sh`.
