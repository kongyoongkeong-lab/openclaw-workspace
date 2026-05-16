#!/usr/bin/env python3
"""
Tool Mapping Matrix for Pentagon System Orchestrator
Deterministic fallback chain: web_search → memory_search → browser → tavily_search → file_fetch → tavily_extract
"""

from typing import Any

# Tool mapping matrix with TRI scores (Tool Retrieval Importance)
# TRI score ranges 0-100; higher = more critical for retrieval tasks
tool_mapping: dict[str, dict[str, Any]] = {
    "web_search": {
        "tri": 95,
        "fallback_chain": [
            "memory_search",
            "browser",
            "tavily_search",
            "file_fetch",
            "tavily_extract"
        ],
        "categories": ["search", "general"],
        "depth_limit": 3,
        "determinism": True
    },
    "memory_search": {
        "tri": 88,
        "fallback_chain": [
            "browser",
            "tavily_search",
            "file_fetch",
            "tavily_extract"
        ],
        "categories": ["memory", "knowledge"],
        "depth_limit": 3,
        "determinism": True
    },
    "browser": {
        "tri": 75,
        "fallback_chain": [
            "tavily_search",
            "file_fetch",
            "tavily_extract"
        ],
        "categories": ["automation", "web"],
        "depth_limit": 3,
        "determinism": True
    },
    "tavily_search": {
        "tri": 92,
        "fallback_chain": [
            "file_fetch",
            "tavily_extract"
        ],
        "categories": ["search", "api"],
        "depth_limit": 3,
        "determinism": True
    },
    "file_fetch": {
        "tri": 80,
        "fallback_chain": [
            "tavily_extract"
        ],
        "categories": ["io", "retrieval"],
        "depth_limit": 2,
        "determinism": True
    },
    "tavily_extract": {
        "tri": 70,
        "fallback_chain": [],
        "categories": ["extraction", "parsing"],
        "depth_limit": 2,
        "determinism": True
    },
    "image": {
        "tri": 65,
        "fallback_chain": [],
        "categories": ["vision", "analysis"],
        "depth_limit": 2,
        "determinism": True
    },
    "image_generate": {
        "tri": 55,
        "fallback_chain": [],
        "categories": ["generation", "creative"],
        "depth_limit": 2,
        "determinism": False
    },
    "pdf": {
        "tri": 68,
        "fallback_chain": [],
        "categories": ["document", "analysis"],
        "depth_limit": 2,
        "determinism": True
    },
    "write": {
        "tri": 50,
        "fallback_chain": [],
        "categories": ["io", "creation"],
        "depth_limit": 2,
        "determinism": True
    },
    "exec": {
        "tri": 45,
        "fallback_chain": [],
        "categories": ["execution", "system"],
        "depth_limit": 1,
        "determinism": False
    },
    "cron": {
        "tri": 40,
        "fallback_chain": [],
        "categories": ["scheduling", "automation"],
        "depth_limit": 2,
        "determinism": True
    },
    "message": {
        "tri": 55,
        "fallback_chain": [],
        "categories": ["communication", "messaging"],
        "depth_limit": 2,
        "determinism": True
    },
    "canvas": {
        "tri": 58,
        "fallback_chain": [],
        "categories": ["canvas", "visual"],
        "depth_limit": 2,
        "determinism": True
    },
    "gateway": {
        "tri": 42,
        "fallback_chain": [],
        "categories": ["infrastructure", "config"],
        "depth_limit": 1,
        "determinism": True
    },
    "session_status": {
        "tri": 35,
        "fallback_chain": [],
        "categories": ["monitoring", "status"],
        "depth_limit": 1,
        "determinism": True
    },
    "sessions_list": {
        "tri": 32,
        "fallback_chain": [],
        "categories": ["monitoring", "session"],
        "depth_limit": 1,
        "determinism": True
    },
    "sessions_history": {
        "tri": 38,
        "fallback_chain": [],
        "categories": ["monitoring", "history"],
        "depth_limit": 1,
        "determinism": True
    },
    "sessions_send": {
        "tri": 48,
        "fallback_chain": [],
        "categories": ["communication", "session"],
        "depth_limit": 1,
        "determinism": True
    },
    "sessions_spawn": {
        "tri": 44,
        "fallback_chain": [],
        "categories": ["orchestration", "subagent"],
        "depth_limit": 2,
        "determinism": False
    },
    "subagents": {
        "tri": 36,
        "fallback_chain": [],
        "categories": ["orchestration", "management"],
        "depth_limit": 1,
        "determinism": True
    },
    "tavily_search": {
        "tri": 92,
        "fallback_chain": [
            "file_fetch",
            "tavily_extract"
        ],
        "categories": ["search", "api"],
        "depth_limit": 3,
        "determinism": True
    },
    "tavily_extract": {
        "tri": 70,
        "fallback_chain": [],
        "categories": ["extraction", "parsing"],
        "depth_limit": 2,
        "determinism": True
    },
    "music_generate": {
        "tri": 52,
        "fallback_chain": [],
        "categories": ["generation", "audio"],
        "depth_limit": 2,
        "determinism": False
    },
    "tts": {
        "tri": 48,
        "fallback_chain": [],
        "categories": ["audio", "speech"],
        "depth_limit": 1,
        "determinism": True
    },
    "video_generate": {
        "tri": 56,
        "fallback_chain": [],
        "categories": ["generation", "video"],
        "depth_limit": 2,
        "determinism": False
    },
    "web_fetch": {
        "tri": 66,
        "fallback_chain": [
            "browser",
            "tavily_search",
            "file_fetch"
        ],
        "categories": ["fetch", "web"],
        "depth_limit": 2,
        "determinism": True
    },
    "agent_team_orchestration": {
        "tri": 82,
        "fallback_chain": [
            "tavily_search",
            "web_fetch",
            "file_fetch"
        ],
        "categories": ["orchestration", "team"],
        "depth_limit": 2,
        "determinism": True
    },
    "skill_vetter": {
        "tri": 78,
        "fallback_chain": [
            "tavily_search",
            "web_fetch"
        ],
        "categories": ["security", "vetting"],
        "depth_limit": 2,
        "determinism": True
    }
}


def get_fallback_chain(tool_name: str) -> list[str]:
    """Get fallback chain for a tool."""
    return tool_mapping.get(tool_name, {}).get("fallback_chain", [])


def get_tool_info(tool_name: str) -> dict[str, Any]:
    """Get complete info for a tool."""
    return tool_mapping.get(tool_name, {})


def get_tool_tris() -> list[tuple[str, int]]:
    """Get list of (tool_name, tri_score) tuples sorted by TRI."""
    return sorted(tool_mapping.items(), key=lambda x: x[1].get("tri", 0), reverse=True)


if __name__ == "__main__":
    import json
    print(json.dumps(tool_mapping, indent=2, default=str))