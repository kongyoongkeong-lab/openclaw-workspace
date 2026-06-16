#!/usr/bin/env python3
"""Calculate usable API context budget from model spec and runtime cap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "config" / "model_runtime.json"


def load_state() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def normalize_model(model: str) -> str:
    if "/" in model:
        model = model.rsplit("/", 1)[-1]
    if model == "gpt-5.5":
        return model
    if model.startswith("gpt-5.5"):
        return "gpt-5.5"
    if model.startswith("gpt-5.4-mini"):
        return "gpt-5.4-mini"
    if model.startswith("gpt-5.4"):
        return "gpt-5.4"
    if model.startswith("gpt-5.2-codex"):
        return "gpt-5.2-codex"
    if model.startswith("gpt-5.2"):
        return "gpt-5.2"
    if model.startswith("gpt-5-codex"):
        return "gpt-5-codex"
    if model.startswith("gpt-5-chat"):
        return "gpt-5-chat-latest"
    return model


def calculate(args: argparse.Namespace, state: dict) -> dict:
    api = state["providers"]["api"]
    policy = api["budget_policy"]
    model = normalize_model(args.model or api["current_runtime_model"])
    specs = api["model_specs"]
    if model not in specs:
        raise SystemExit(f"Unknown model spec: {model}")

    spec = specs[model]
    model_window = int(spec["context_window_tokens"])
    configured_window = api.get("configured_runtime_context_window_tokens")
    current_session_window = args.current_session_window or api.get("current_session_context_window_tokens")
    if args.current_session:
        runtime_window = args.runtime_window or int(current_session_window or configured_window or model_window)
        runtime_scope = "current_session"
    else:
        runtime_window = args.runtime_window or int(configured_window or current_session_window or model_window)
        runtime_scope = "configured_runtime"
    effective_window = min(model_window, runtime_window)

    reserve_output = min(
        int(effective_window * float(policy["reserve_output_ratio"])),
        int(spec["max_output_tokens"]),
    )
    reserve_reasoning = int(effective_window * float(policy["reserve_reasoning_ratio"]))
    usable_input = max(effective_window - reserve_output - reserve_reasoning, 0)
    target_fill = int(effective_window * float(policy["target_fill_ratio"]))
    soft_compact = int(effective_window * float(policy["soft_compact_ratio"]))
    hard_compact = int(effective_window * float(policy["hard_compact_ratio"]))
    absolute_stop = int(effective_window * float(policy["absolute_stop_ratio"]))

    return {
        "model": model,
        "model_context_window_tokens": model_window,
        "runtime_context_window_tokens": runtime_window,
        "runtime_scope": runtime_scope,
        "effective_context_window_tokens": effective_window,
        "usable_input_tokens": usable_input,
        "reserved_output_tokens": reserve_output,
        "reserved_reasoning_tokens": reserve_reasoning,
        "target_fill_tokens": target_fill,
        "soft_compact_tokens": soft_compact,
        "hard_compact_tokens": hard_compact,
        "absolute_stop_tokens": absolute_stop,
        "source": spec["source"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="API model id. Defaults to configured current model.")
    parser.add_argument("--runtime-window", type=int, help="Observed runtime/session context cap.")
    parser.add_argument(
        "--current-session",
        action="store_true",
        help="Use the already-running session cap instead of the configured runtime cap.",
    )
    parser.add_argument(
        "--current-session-window",
        type=int,
        help="Observed current session context cap. Use this with --current-session when session_status has fresher data than config.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic budget math self-test.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        state = {
            "providers": {
                "api": {
                    "current_runtime_model": "gpt-5.2",
                    "configured_runtime_context_window_tokens": 1000,
                    "budget_policy": {
                        "reserve_output_ratio": 0.1,
                        "reserve_reasoning_ratio": 0.1,
                        "target_fill_ratio": 0.5,
                        "soft_compact_ratio": 0.6,
                        "hard_compact_ratio": 0.8,
                        "absolute_stop_ratio": 0.9,
                    },
                    "model_specs": {
                        "gpt-5.2": {
                            "context_window_tokens": 2000,
                            "max_output_tokens": 500,
                            "source": "self-test",
                        }
                    },
                }
            }
        }
        test_args = argparse.Namespace(model=None, runtime_window=None, current_session=False, current_session_window=None)
        result = calculate(test_args, state)
        assert result["effective_context_window_tokens"] == 1000
        assert result["usable_input_tokens"] == 800
        print("PASS: api context budget self-test passed.")
        return 0
    result = calculate(args, load_state())
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
