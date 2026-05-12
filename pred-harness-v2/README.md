# Predictability Harness V2
**Deterministic Execution Contract** for OpenClaw LLM Applications

## Overview
This harness implements a **Deterministic Execution Contract** with architectural enhancements for:
- Execution records with hidden state capture
- Determinism enforcement across inference/scheduler/retrieval layers
- Validation layer with drift severity scoring
- Phase A/B/C test runners
- Full replay validation

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Predictability Harness V2                  │
├─────────────────────────────────────────────────────────────┤
│  Execution Record Layer                                       │
│  ├─ ADDITIONAL FIELDS:                                         │
│  │   • retrieval_hash: SHA-256 of retrieval snapshot           │
│  │   • signal_vector: governance state capture                  │
│  │   • model_config: inference parameters snapshot              │
│  │   • cycle_id: sequential identifier for replay comparison    │
│  └─ HARD REQUIREMENTS:                                         │
│      • temperature = 0.0 (mandatory)                           │
│      • fixed seed (seed=42, mandatory)                         │
│      • fixed retrieval top_k (top_k=3, mandatory)              │
│      • identical context ordering (no dynamic reordering)      │
├─────────────────────────────────────────────────────────────┤
│  Validation Layer                                             │
│  ├─ validate_determinism(rec1, rec2) → comprehensive report   │
│  ├─ compute_drift_severity(consistency_dict) → severity score │
│  └─ Metrics:                                                   │
│      • ContextReplayConsistency: identical context reconstruction (target: 1.0)   │
│      • RetrievalHashVariance: retrieval state divergence (target: < 0.02)         │
│      • DeterminismIndex (DI): (oc + rc + sc + gc + crc) / 5 (target: > 0.99)     │
├─────────────────────────────────────────────────────────────┤
│  Test Phases                                                  │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Phase A: Static Replay (10x identical cycles)         │     │
│  │   • fixed seed                                        │     │
│  │   • fixed retrieval                                   │     │
│  │   • frozen governance                                 │     │
│  │   • frozen context                                    │     │
│  │   • Goal: DI > 0.99                                   │     │
│  └─────────────────────────────────────────────────────┘     │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Phase B: Retrieval Perturbation                      │     │
│  │   • ±1 position changes in retrieval ordering         │     │
│  │   • Measure: output sensitivity, governance stability │     │
│  │   • Goal: bounded divergence (< 0.05 variance)        │     │
│  └─────────────────────────────────────────────────────┘     │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ Phase C: Governance Perturbation                     │     │
│  │   • Inject controlled telemetry noise                  │     │
│  │   • Verify: UCG stability, scheduler determinism      │     │
│  │   • No recursive escalation                            │     │
│  │   • Goal: governance action variance = 0               │     │
│  └─────────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│  Deterministic Replay Validator                               │
│  • Record all execution_records in immutable log             │
│  • Compute DI after each cycle                               │
│  • Flag any DI drop below 0.99                               │
│  • Generate drift report if DI < 0.98                        │
└─────────────────────────────────────────────────────────────┘
```

## Files
- `execution_record.py` - Execution record structure with ADDITIONAL FIELDS
- `determinism_enforcer.py` - Determinism enforcement rules
- `validation_layer.py` - Validation functions and drift analysis
- `test_phase_a.py` - Static replay test runner
- `test_phase_b.py` - Retrieval perturbation test runner
- `test_phase_c.py` - Governance perturbation test runner
- `deterministic_replay_validator.py` - Full replay validator
- `run_pred_harness_v2.py` - Main harness runner
- `README.md` - This file

## Usage
```bash
# Run the harness
python3 run_pred_harness_v2.py

# Run individual phases
python3 test_phase_a.py   # Static replay test
python3 test_phase_b.py   # Retrieval perturbation test
python3 test_phase_c.py   # Governance perturbation test

# Run replay validation only
python3 deterministic_replay_validator.py
```

## Metrics
- **Determinism Index (DI)**: (oc + rc + sc + gc + crc) / 5 (target: > 0.99)
- **Context Replay Consistency**: identical context reconstruction (target: 1.0)
- **Retrieval Hash Variance**: retrieval state divergence (target: < 0.02)
- **Governance Stability**: governance state preservation (target: 1.0)
- **Output Consistency**: output hash equality (target: True)
- **Semantic Variance**: semantic equivalence across cycles (target: < 0.05)

## Execution Record Fields (ADDITIONAL)
```python
ExecutionRecord(
    output: str,                    # Model output
    retrieval_hash: str,            # SHA-256 of retrieval state
    signal_vector: str,             # Governance state
    model_config: Dict,             # Inference parameters
    cycle_id: int,                  # Sequential identifier
    retrieval_ids: List[str],       # Retrieved document IDs
    freeze_config: Dict             # Frozen config snapshot
)
```

## Determinism Contract
```
TEMPERATURE=0.0 (mandatory)
SEED=42 (mandatory)
TOP_K=3 (mandatory)
CONTEXT_ORDERING=static (no dynamic reordering)
QUEUE_ORDERING=fifo (no adaptive arbitration)
STATIC_PRIORITY=True
DEDUPLICATE_RETRIEVAL_IDS=True
NO_TIMESTAMP_WEIGHTING=True
FREEZE_SIGNAL_VECTOR=True
GOVERNANCE_HASH_REQUIRED=True
```

## Test Results Format
```json
{
  "harness": "Predictability Harness V2",
  "timestamp": "2024-01-01T12:00:00",
  "phases": {
    "static_replay": {
      "cycles": 10,
      "average_di": 0.999,
      "all_cycles_pass": true
    },
    "retrieval_perturbation": {
      "test_cases": 5,
      "average_variance": 0.012,
      "variance_within_bounds": true
    },
    "governance_perturbation": {
      "governance_stable": true,
      "scheduler_consistent": true,
      "escalation_detected": false
    }
  },
  "summary": {
    "all_phases_passed": true,
    "average_di": 0.999,
    "di_target": 0.99
  }
}
```

## License
Proprietary to OpenClaw Labs.
