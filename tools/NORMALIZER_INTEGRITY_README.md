# Normalizer Integrity Harness 🛡️

## Purpose

Verify 4 critical boundaries of your signal normalizer foundation:

```
1. deterministic      → normalize(x) == normalize(x)
2. idempotent         → normalize(normalize(x)) == normalize(x)
3. replay stable      → replay(trace) == canonical_signal_set
4. single-origin      → signal.dependencies ⊆ {RAW_SIGNAL}
```

## Why This Matters

```
Corrupted normalization foundation → IRREVERSIBLE CASCADE

Failure Modes:
- Semantic Creep: bucket → label → inference
- Hidden Aggregation: signal = f(signal1, signal2, ...)
- Replay Divergence: normalize(trace) != normalize(trace')
```

## Usage

### Run All Tests

```bash
python normalizer_harness.py --all
```

### Run Specific Tests

```bash
# Determinism only
python normalizer_harness.py --test-determinism

# Replay stability with trace file
python normalizer_harness.py --trace trace.json --test-replay
```

### Continuous Integration

Add to your CI pipeline:

```yaml
steps:
  - run: |
      python normalizer_harness.py --all --signals latency,retry,entropy
      test -f /workspace/tools/corruption_log.txt || exit 1
```

## Test Results

Results are logged to:
- `/workspace/tools/integrity_results.jsonl` - All test results
- `/workspace/tools/corruption_log.txt` - Failed tests only

## Architecture

```
┌─────────────────────────────────────┐
│   Signal Normalizer                  │
│   (Your actual normalizer logic)      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Integrity Harness                  │
│   - Determinism checker              │
│   - Idempotency validator            │
│   - Replay stability enforcer        │
│   - Single-origin purity monitor     │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   Trace Integrity Layer              │
│   - Canonicalization                 │
│   - Serialization                   │
└─────────────────────────────────────┘
```

## Key Principle

> Observability before adaptation
> Compression before interpretation
> Causality before optimization

This harness ensures your normalizer foundation stays intact before you add:
- routing
- RAG
- MCP
- adaptive execution

## Next Phase

Once all 4 tests pass consistently:

```
Phase: Normalizer Verification Harness
- Replay trace integrity
- Canonical signal set generation
- Trace serialization validation
- Dependency purity checking
```

---

**Status:** ✅ Active | 🚀 Strict Long-Horizon Stability Mode
