# Pentagon Vault - Hardware Baseline
**Initiated:** 2026-05-08 22:26 GMT+8
**GPU:** NVIDIA GeForce RTX 4070 SUPER (12GB)
**VRAM Usage:** 10069/12282 MiB (82%)
**Status:** OPERATIONAL

## Immutable Facts
- **Primary Model:** qwen3.5:9b (Local)
- **Fallback Model:** gemini-2.5-flash-lite (Cloud)
- **VRAM Ceiling:** 9.5GB (hard limit for local tasks)
- **Base Path:** /home/jason2ykk/.openclaw/workspace/

## Agent Registry
- @main (Orchestrator): gemini-2.5-flash-lite
- @intel (Research): qwen3.5:4b
- @ops (Execution): qwen3.5:4b
- @comms (Communication): qwen3.5:4b
- @sentinel (Guardian): qwen3.5:4b

## Token Budgets (Cumulative)
- @intel: 2000 tokens
- @ops: 3000 tokens
- @comms: 1500 tokens
- @sentinel: 1000 tokens

## Cache Ratios (Target: 70-90%)
- LTM Cache: 82%
- Vector Cache: 65%
- Context Cache: 78%
