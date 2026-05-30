#!/usr/bin/env python3
"""Hybrid-runtime protocol consistency audit for Jason's OpenClaw workspace."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAIL: list[str] = []
WARN: list[str] = []

REQUIRED_FILES = [
    "AGENTS.md",
    ".github/copilot-instructions.md",
    "daily_news.md",
    "daily_ai.md",
    "PROTOCOL_INVARIANTS.md",
    "CURRENT_RUNTIME.md",
    "PROVIDER_STATUS.md",
    "agent_registry.json",
    "tools/check_gpu.sh",
    "tools/codex_quota_preflight.py",
    "tools/tavily_key_preflight.py",
]

ROLE_FILES = [
    "intel/AGENTS.md",
    "ops/AGENTS.md",
    "comms/AGENTS.md",
    "sentinel/AGENTS.md",
    "intel/HEARTBEAT.md",
    "ops/HEARTBEAT.md",
    "comms/HEARTBEAT.md",
    "sentinel/HEARTBEAT.md",
]

POLICY_FILES = [
    "AGENTS.md",
    ".github/copilot-instructions.md",
    "docs/github_governance.md",
    "SOUL.md",
    "TOOLS.md",
    "PROTOCOL_INVARIANTS.md",
    "CURRENT_RUNTIME.md",
    "PROVIDER_STATUS.md",
    *ROLE_FILES,
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def exists(path: str) -> bool:
    return (ROOT / path).exists()


def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        if not exists(rel):
            FAIL.append(f"missing required file: {rel}")


def check_json(path: str) -> None:
    if not exists(path):
        return
    try:
        json.loads(read(path))
    except Exception as exc:  # noqa: BLE001
        FAIL.append(f"invalid JSON {path}: {exc}")


def check_registry() -> None:
    if not exists("agent_registry.json"):
        return
    registry = json.loads(read("agent_registry.json"))
    agents = registry.get("agents", {})
    for agent in ["main", "intel", "ops", "comms", "sentinel"]:
        item = agents.get(agent)
        if not item:
            FAIL.append(f"agent_registry.json missing agent: {agent}")
            continue
        if item.get("agentId") != agent:
            FAIL.append(f"agent_registry.json agentId mismatch for {agent}")
        if "restricted_actions" not in item and agent != "main":
            WARN.append(f"agent_registry.json missing restricted_actions for {agent}")
    bad = "legacy sessions_send agent parameter"
    if bad not in json.dumps(registry):
        WARN.append("agent_registry.json should explicitly ban the stale sessions_send agent parameter")


def check_hardware_policy() -> None:
    stale_patterns = [
        (re.compile(r"4070\s+Ti", re.I), "stale GPU model reference"),
        (re.compile(r"90%\+", re.I), "stale 90%+ GPU utilization target"),
        (re.compile(r"\b98%\b", re.I), "stale 98% emergency threshold"),
    ]
    for rel in POLICY_FILES:
        if not exists(rel):
            continue
        text = read(rel)
        for pattern, label in stale_patterns:
            if pattern.search(text):
                FAIL.append(f"{label}: {rel}")


def check_model_coordination_policy() -> None:
    if not exists("config/model_runtime.json"):
        return
    try:
        model_runtime = json.loads(read("config/model_runtime.json"))
    except Exception as exc:  # noqa: BLE001
        FAIL.append(f"invalid JSON config/model_runtime.json: {exc}")
        return

    if model_runtime.get("active_mode") != "hybrid":
        FAIL.append("config/model_runtime.json active_mode is not hybrid")
    if model_runtime.get("default_mode") != "hybrid":
        FAIL.append("config/model_runtime.json default_mode is not hybrid")

    hardware = model_runtime.get("hardware", {})
    if hardware.get("gpu") != "NVIDIA GeForce RTX 4070 SUPER":
        FAIL.append("config/model_runtime.json GPU baseline is not RTX 4070 SUPER")
    if hardware.get("vram_hard_ceiling_mib") != 9728:
        FAIL.append("config/model_runtime.json VRAM hard ceiling is not 9728 MiB")

    providers = model_runtime.get("providers", {})
    api_role = providers.get("api", {}).get("role")
    ollama = providers.get("ollama", {})
    if api_role != "orchestrator":
        FAIL.append("config/model_runtime.json API provider role is not orchestrator")
    if ollama.get("role") != "local_worker":
        FAIL.append("config/model_runtime.json Ollama provider role is not local_worker")

    configured_models = set(ollama.get("models", {}).values())
    required_models = {"qwen3.5:9b", "qwen3.5:4b", "qwen3.5:2b"}
    missing = sorted(required_models - configured_models)
    if missing:
        FAIL.append(f"config/model_runtime.json missing required Ollama models: {', '.join(missing)}")

    if exists("CURRENT_RUNTIME.md"):
        current = read("CURRENT_RUNTIME.md")
        required_phrases = [
            "Active workspace model mode: hybrid",
            "Ollama role: local worker",
            "GPU: NVIDIA GeForce RTX 4070 SUPER",
            "VRAM hard ceiling for local inference: 9728 MiB",
        ]
        for phrase in required_phrases:
            if phrase not in current:
                FAIL.append(f"CURRENT_RUNTIME.md missing model coordination phrase: {phrase}")

    if exists("docs/model_runtime_strategy.md"):
        strategy = read("docs/model_runtime_strategy.md")
        if re.search(r"cloud-native-only|do not route to local Ollama|do not route to local GPU", strategy, re.I):
            FAIL.append("docs/model_runtime_strategy.md contains cloud-only policy that conflicts with hybrid runtime")


def check_copilot_policy() -> None:
    path = ".github/copilot-instructions.md"
    if not exists(path):
        return
    text = read(path)
    required_phrases = [
        "active model policy as hybrid",
        "API/Codex handles orchestration",
        "Ollama handles compact/private worker tasks only after GPU preflight passes",
        "Do not replace hybrid mode with cloud-native-only",
        "Do not write to Qdrant unless explicit approval",
        "Never suggest `git add .`",
        "python3 scripts/protocol_audit.py",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            FAIL.append(f"{path} missing required guardrail phrase: {phrase}")


def check_shortcut_repair_surface() -> None:
    if exists("shortcuts.md"):
        text = read("shortcuts.md")
        stale_phrases = [
            "daily_news.md` 和 `daily_ai.md` 当前本地缺失",
            "tools/codex_quota_preflight.py`, `tools/tavily_key_preflight.py` 当前本地缺失",
            "当前本地缺失 | 待接入",
        ]
        for phrase in stale_phrases:
            if phrase in text:
                FAIL.append(f"shortcuts.md still claims repaired shortcut artifact is missing: {phrase}")
    workflow_requirements = {
        "daily_news.md": [
            "Mandatory Cache Gate",
            "Archive filename: `YYYY-MM-DD_daily_news.md`",
            "刷新新闻",
            "Secret",
        ],
        "daily_ai.md": [
            "Freshness window: last 7 days",
            "Archive filename: `YYYY-MM-DD_daily_ai.md`",
            "Mandatory Cache Gate",
        ],
    }
    for rel, phrases in workflow_requirements.items():
        if not exists(rel):
            continue
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                FAIL.append(f"{rel} missing workflow phrase: {phrase}")
    tool_requirements = {
        "tools/codex_quota_preflight.py": ["Secret policy", "openai-codex", "--dry-run"],
        "tools/tavily_key_preflight.py": ["Secret policy", "TAVILY_API_KEY", "--check-all"],
    }
    for rel, phrases in tool_requirements.items():
        if not exists(rel):
            continue
        text = read(rel)
        for phrase in phrases:
            if phrase not in text:
                FAIL.append(f"{rel} missing required safe-preflight phrase: {phrase}")
    if exists("docs/github_governance.md"):
        governance = read("docs/github_governance.md")
        required = [
            "Remote Backup Handling",
            "Do not restore,",
            "git merge",
            "Branch-wide restore",
            "Rewrite the behavior for the current local hybrid runtime",
        ]
        for phrase in required:
            if phrase not in governance:
                FAIL.append(f"docs/github_governance.md missing remote-backup guardrail: {phrase}")


def check_qdrant_write_policy() -> None:
    for rel in POLICY_FILES:
        if not exists(rel):
            continue
        text = read(rel)
        mentions_qdrant = re.search(r"Qdrant|vectori[sz]e|vector store", text, re.I)
        write_like = re.search(r"write|store|upsert|compact database|vectori[sz]e incoming", text, re.I)
        approval = re.search(r"explicit approval|approval required|read-only", text, re.I)
        if mentions_qdrant and write_like and not approval:
            FAIL.append(f"Qdrant/write-like instruction lacks approval language: {rel}")


def check_a2a_syntax() -> None:
    for rel in ["SOUL.md", "TOOLS.md", "AGENTS.md"]:
        if exists(rel) and "sessions_send(agent=" in read(rel):
            FAIL.append(f"stale A2A syntax with sessions_send agent parameter found: {rel}")


def check_skill_surface() -> None:
    agent_skill_dirs = {
        agent: sorted(p.parent.name for p in (ROOT / agent / "skills").glob("*/SKILL.md"))
        for agent in ["intel", "ops", "comms", "sentinel"]
        if (ROOT / agent / "skills").exists()
    }
    if len(agent_skill_dirs) < 4:
        WARN.append("not all subagent skill directories are present for skill-surface audit")
        return
    common = set.intersection(*(set(v) for v in agent_skill_dirs.values()))
    if len(common) >= 20:
        WARN.append(f"subagent skill surface remains broad: {len(common)} skills common to all subagents")
    if any("self-evolving-skill-1.0.2" in v for v in agent_skill_dirs.values()):
        WARN.append("self-evolving-skill-1.0.2 remains installed under one or more subagents; trust decision still required")


def check_secret_residue() -> None:
    models_path = Path("/home/jason2ykk/.openclaw/agents/main/agent/models.json")
    if not models_path.exists():
        return
    try:
        data = json.loads(models_path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        WARN.append("could not parse generated main agent models.json for secret residue check")
        return
    providers = data.get("providers", {})
    for name, provider in providers.items():
        if isinstance(provider, dict) and provider.get("apiKey"):
            WARN.append(f"generated agent models.json still has provider apiKey residue: {name}")


def main() -> int:
    check_required_files()
    check_json("agent_registry.json")
    check_json("config/model_runtime.json")
    check_json("config/protocol_mode.json")
    check_registry()
    check_hardware_policy()
    check_model_coordination_policy()
    check_copilot_policy()
    check_shortcut_repair_surface()
    check_qdrant_write_policy()
    check_a2a_syntax()
    check_skill_surface()
    check_secret_residue()

    print("# Hybrid Protocol Audit Result")
    if WARN:
        print("\n## Warnings")
        for item in WARN:
            print(f"- WARN: {item}")
    if FAIL:
        print("\n## Failures")
        for item in FAIL:
            print(f"- FAIL: {item}")
        return 1
    print("\nPASS: no blocking hybrid protocol violations found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
