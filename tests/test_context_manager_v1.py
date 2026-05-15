#!/usr/bin/env python3
"""Regression tests for Context Manager v1."""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path('/home/jason2ykk/.openclaw/workspace')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'runtime'))

from render.render_policy import RenderPolicy
from context.context_budget import get_context_policy
from context.context_planner import ContextPlanner
from context.context_guard import validate_context, guarded_model_call


class TestProgressCommandRegression(unittest.TestCase):
    def test_progress_stable_has_no_telemetry(self):
        expected = "Stable. No user action required."
        result = RenderPolicy.render_progress()
        self.assertEqual(result, expected)
        for forbidden in (
            "GAF", "RPR", "Determinism", "IdleOccupancy", "VRAM",
            "Context Used", "Event Loop", "MTS Observer", "Context Guard",
            "🚀", "🤖", "Table", "Metrics",
        ):
            self.assertNotIn(forbidden, result)

    def test_progress_exact_one_line(self):
        self.assertEqual(RenderPolicy.route_render("progress", ""), "Stable. No user action required.")
        self.assertNotIn("\n", RenderPolicy.route_render("progress", ""))

    def test_stable_string_length_is_32(self):
        self.assertEqual(len("Stable. No user action required."), 32)
        self.assertEqual(len(RenderPolicy.generate_stable_response()), 32)


class TestContextManagerV1(unittest.TestCase):
    def test_get_context_policy_has_canonical_keys(self):
        policy = get_context_policy()
        expected = {
            "max_context_tokens": 8192,
            "warning_threshold_tokens": 6850,
            "block_threshold_tokens": 6963,
            "hard_limit_tokens": 8192,
            "burst_ceiling_tokens": 9536,
            "output_reserve_tokens": 2000,
        }
        for key, value in expected.items():
            self.assertEqual(policy[key], value)

    def test_should_load_summary_no_nameerror(self):
        planner = ContextPlanner()
        self.assertFalse(planner.should_load_summary(100))
        self.assertTrue(planner.should_load_summary(6850))

    def test_summary_loaded_only_when_needed(self):
        normal = validate_context("short prompt")
        self.assertTrue(normal.allowed)
        self.assertFalse(normal.summary_loaded)

        pressured = validate_context("x " * 7600)
        self.assertTrue(pressured.allowed)
        self.assertTrue(pressured.summary_loaded)
        self.assertIn("short", normal.final_context)

    def test_live_model_path_calls_context_manager_before_inference(self):
        calls = []

        def fake_model(prompt):
            calls.append(prompt)
            return "model-result"

        result = guarded_model_call(fake_model, "normal prompt")
        self.assertEqual(result, "model-result")
        self.assertEqual(len(calls), 1)

    def test_oversized_prompt_blocked_before_model_call(self):
        calls = []

        def fake_model(prompt):
            calls.append(prompt)
            return "should-not-run"

        with self.assertRaises(RuntimeError):
            guarded_model_call(fake_model, "x " * 9000)
        self.assertEqual(calls, [])

    def test_context_warning_logged_externally(self):
        log_path = ROOT / "runtime/logs/context_budget.log"
        before = log_path.read_text(errors="ignore") if log_path.exists() else ""
        decision = validate_context("x " * 7600)
        after = log_path.read_text(errors="ignore") if log_path.exists() else ""
        self.assertTrue(decision.allowed)
        self.assertGreaterEqual(len(after), len(before))
        self.assertIn("Context warning before inference", after)

    def test_show_full_telemetry_preserves_supplied_payload(self):
        payload = "GPU: 74% | VRAM: 69% | Invariants: HOLDING"
        self.assertEqual(RenderPolicy.route_render("show full telemetry", payload), payload)

    def test_normal_question_not_suppressed(self):
        message = "Use the Actions tab, inspect the workflow run, and confirm required checks passed."
        self.assertEqual(RenderPolicy.route_render("How do I verify GitHub CI?", message), message)


if __name__ == '__main__':
    unittest.main()
