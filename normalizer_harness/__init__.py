"""
Normalizer Verification Harness Skeleton

Purpose: Binary invariant enforcement only.
- Determinism: normalize(x) == normalize(x)
- Idempotency: normalize(normalize(x)) == normalize(x)
- Replay Stability: replay(trace) == canonical_signal_set
- Single-Origin Purity: signal.dependencies == RAW_ONLY

NO inference. NO scoring. NO aggregation.
"""
