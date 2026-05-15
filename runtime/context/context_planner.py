#!/usr/bin/env python3
"""Context planner for structured context budgeting and summary loading."""

import os
import logging

try:
    from .context_budget import (
        check_context_budget,
        load_memory_summary,
        reserve_output_buffer,
        get_context_policy,
    )
except ImportError:  # support direct sys.path imports used by local tests
    from context_budget import (
        check_context_budget,
        load_memory_summary,
        reserve_output_buffer,
        get_context_policy,
    )

# Configure logging
LOG_DIR = "/home/jason2ykk/.openclaw/workspace/runtime/logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("context_planner")
logger.setLevel(logging.INFO)

try:
    from logging.handlers import RotatingFileHandler
    fh = RotatingFileHandler(
        "/home/jason2ykk/.openclaw/workspace/runtime/logs/context_budget.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s"
    )
    fh.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(fh)
except Exception as e:
    logger.warning(f"Failed to setup rotating file handler: {e}")


class ContextPlanner:
    """
    Context Manager v1 - Deterministic context budgeting.
    No autonomous governance. No self-repair.
    """

    def __init__(self, context_limit: int = 8192, heavy_mode: bool = False):
        self.context_limit = context_limit
        self.heavy_mode = heavy_mode
        self.output_buffer = reserve_output_buffer(context_limit)
        self.used_tokens = 0
        self.max_local_context = 32768

    def plan(self, prompt: str, system: str = None, messages: list = None) -> tuple[bool, str]:
        """
        Plan and execute context budget check.
        Returns: (allowed, message)
        """
        self.used_tokens = self.used_tokens + self.output_buffer
        allowed, msg, tokens = check_context_budget(
            prompt=prompt,
            system=system,
            messages=messages,
            context_limit=self.context_limit,
            heavy_mode=self.heavy_mode
        )
        self.used_tokens = tokens  # Reset to actual used tokens

        if not allowed:
            logger.warning(f"Context blocked: {msg} (used={self.used_tokens}, limit={self.context_limit})")
            return False, msg

        logger.debug(f"Context OK: used={self.used_tokens}/{self.context_limit}, msg={msg[:50]}")
        return True, msg

    def should_load_summary(self, current_usage: float) -> bool:
        """
        Load state_summary.md only when needed (when context is tight).
        """
        policy = get_context_policy()
        return current_usage >= policy["warning_threshold_tokens"]

    def load_summary_on_demand(self):
        """Load state_summary.md when context budget allows."""
        summary = load_memory_summary()
        if summary:
            logger.info("Loaded state_summary.md on-demand")
            return summary
        return None

    def get_usage_report(self) -> dict:
        """
        Minimal usage report (no chat spam).
        """
        return {
            "context_limit": self.context_limit,
            "output_buffer": self.output_buffer,
            "max_local_context": self.max_local_context,
            "used_tokens": self.used_tokens
        }

    def get_policy(self) -> dict:
        """Return current policy constants."""
        return get_context_policy()


def create_planner(context_limit: int = 8192, heavy_mode: bool = False) -> ContextPlanner:
    """Factory function to create a ContextPlanner."""
    return ContextPlanner(context_limit=context_limit, heavy_mode=heavy_mode)


if __name__ == "__main__":
    import sys
    planner = create_planner()
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    allowed, msg = planner.plan(prompt)
    print(f"Allowed: {allowed}, Message: {msg}")
