#!/usr/bin/env bash
# ============================================================
# INSTRUMENTATION STRESS VALIDATION
# Phase 2: Burst + Interleaving + Rapid-Fire Tests
# ============================================================

set -euo pipefail

# ============================================================
# CONFIGURATION
# ============================================================
WORKSPACE="${OPENCLAW_WORKSPACE:-/home/jason2ykk/.openclaw/workspace}"
CAUSAL_LOG_DIR="${CAUSAL_LOG_DIR:-${WORKSPACE}/causal_logs/raw_events}"
METRICS_AGG_DIR="${METRICS_AGG_DIR:-${WORKSPACE}/causal_logs/metrics_agg}"
VALIDATION_LOG="${CAUSAL_LOG_DIR}/instrumentation_stress_validation.log"

# Event counts
BURST_COUNT=100
INTERLEAVE_ROUNDS=10
RAPID_COUNT=50
DELAY_MS=1

# ============================================================
# STRESS TEST FUNCTIONS
# ============================================================

# Test A: Burst ingestion
run_burst_test() {
    local probe_id="$1"
    local count="$2"
    local delay="$3"
    
    echo "=== TEST A: Burst Ingestion ($probe_id x $count events) ==="
    
    local start_time=$(date +%s%3N)
    local success=0
    local failures=0
    
    for i in $(seq 1 "$count"); do
        # Inject event
        log_raw_event "$probe_id" "stress_burst" "BURST_INJECTION" "$i"
        
        # Apply delay
        if [[ "$delay" -gt 0 ]]; then
            sleep "0.$(printf '%03d' $((i % 100)))"
        fi
        
        success=$((success + 1))
    done
    
    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))
    
    echo "✓ Burst ingestion complete: $success/$count events injected"
    echo "  Duration: ${duration}ms"
    
    # Validate count
    local actual_count=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_id}.log")
    local base_count=$(grep -c "event=SEQUENCE_CHECK" "${CAUSAL_LOG_DIR}/${probe_id}.log" 2>/dev/null || echo "0")
    local total_expected=$((base_count + count))
    
    if [[ "$actual_count" == "$total_expected" ]]; then
        echo "✓ Event count validated: $actual_count == $total_expected"
        return 0
    else
        echo "✗ Event count mismatch: actual=$actual_count, expected=$total_expected"
        return 1
    fi
}

# Test B: Interleaved probe execution
run_interleave_test() {
    local rounds="$1"
    
    echo ""
    echo "=== TEST B: Interleaved Probe Execution ($rounds rounds) ==="
    
    local probe_ids=("q4v9qs" "7wo52k" "1e8r9u" "fdd3u2" "7pc5ie" "j13nsu" "causal_hash_probe")
    
    for round in $(seq 1 "$rounds"); do
        for probe_id in "${probe_ids[@]}"; do
            log_raw_event "$probe_id" "stress_interleave" "INTERLEAVED" "$round"
        done
    done
    
    echo "✓ Interleaved execution complete: $rounds rounds"
    
    # Validate each probe maintained separation
    local all_clean=true
    for probe_id in "${probe_ids[@]}"; do
        local probe_count=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_id}.log")
        local base_count=$(grep -c "event=SEQUENCE_CHECK" "${CAUSAL_LOG_DIR}/${probe_id}.log" 2>/dev/null || echo "0")
        local expected=$((base_count + rounds))
        
        if [[ "$probe_count" == "$expected" ]]; then
            echo "  ✓ $probe_id: $probe_count events (no leakage)"
        else
            echo "  ✗ $probe_id: $probe_count events, expected $expected"
            all_clean=false
        fi
    done
    
    if [[ "$all_clean" == "true" ]]; then
        echo "✓ No probe cross-talk detected"
        return 0
    else
        echo "✗ Probe cross-talk detected"
        return 1
    fi
}

# Test C: Rapid-fire ingestion
run_rapidfire_test() {
    local count="$1"
    
    echo ""
    echo "=== TEST C: Rapid-Fire Ingestion ($count events, ${DELAY_MS}ms delay) ==="
    
    local probe_ids=("q4v9qs" "7wo52k" "1e8r9u" "fdd3u2" "7pc5ie" "j13nsu")
    local all_ok=true
    
    for probe_id in "${probe_ids[@]}"; do
        local base_count=$(grep -c "event=SEQUENCE_CHECK" "${CAUSAL_LOG_DIR}/${probe_id}.log" 2>/dev/null || echo "0")
        local expected=$((base_count + count))
        
        for i in $(seq 1 "$count"); do
            log_raw_event "$probe_id" "stress_rapidfire" "RAPIDFIRE" "$i"
            sleep "0.$((i % 50))"
        done
        
        local actual_count=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_id}.log")
        
        if [[ "$actual_count" == "$expected" ]]; then
            echo "  ✓ $probe_id: $actual_count events (monotonic)"
        else
            echo "  ✗ $probe_id: actual=$actual_count, expected=$expected"
            all_ok=false
        fi
    done
    
    if [[ "$all_ok" == "true" ]]; then
        echo "✓ Rapid-fire test passed: monotonicity preserved"
        return 0
    else
        echo "✗ Rapid-fire test failed: race conditions detected"
        return 1
    fi
}

# Validation helpers
log_raw_event() {
    local probe_id="$1"
    local metric="$2"
    local event_type="$3"
    local value="$4"
    
    local SEQ_COUNTER_FILE="${CAUSAL_LOG_DIR}/sequence_counter"
    
    if [[ -f "${SEQ_COUNTER_FILE}" ]]; then
        local CURRENT_SEQ=$(cat "${SEQ_COUNTER_FILE}")
        CURRENT_SEQ=$((CURRENT_SEQ + 1))
        echo "${CURRENT_SEQ}" > "${SEQ_COUNTER_FILE}"
    else
        CURRENT_SEQ=1
        echo "${CURRENT_SEQ}" > "${SEQ_COUNTER_FILE}"
    fi
    
    cat >> "${CAUSAL_LOG_DIR}/${probe_id}.log" << EOF
[${CURRENT_SEQ}]$(date +%s%3N) probe_id=${probe_id} metric=${metric} event=${event_type} value=${value} seq=${CURRENT_SEQ}
EOF
}

# ============================================================
# MAIN
# ============================================================

main() {
    mkdir -p "${CAUSAL_LOG_DIR}" "${METRICS_AGG_DIR}"
    
    echo "========================================="
    echo "INSTRUMENTATION STRESS VALIDATION"
    echo "========================================="
    echo ""
    echo "Configuration:"
    echo "  Burst count: $BURST_COUNT"
    echo "  Interleave rounds: $INTERLEAVE_ROUNDS"
    echo "  Rapid-fire count: $RAPID_COUNT"
    echo "  Delay: ${DELAY_MS}ms"
    echo ""
    
    # Capture initial counts
    echo "Capturing initial state..."
    for probe_id in q4v9qs 7wo52k 1e8r9u fdd3u2 7pc5ie j13nsu; do
        local initial_count=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_id}.log")
        echo "  $probe_id: $initial_count events (baseline)"
    done
    
    echo ""
    
    # Test A: Burst ingestion
    run_burst_test "q4v9qs" "$BURST_COUNT" "$DELAY_MS"
    run_burst_test "7wo52k" "$BURST_COUNT" "$DELAY_MS"
    run_burst_test "1e8r9u" "$RAPID_COUNT" "$DELAY_MS"
    
    # Test B: Interleaved execution
    run_interleave_test "$INTERLEAVE_ROUNDS"
    
    # Test C: Rapid-fire
    run_rapidfire_test "$RAPID_COUNT"
    
    echo ""
    echo "========================================="
    echo "STRESS VALIDATION COMPLETE"
    echo "========================================="
    
    # Final validation summary
    echo ""
    echo "Final Validation Summary:"
    echo "========================="
    
    for probe_id in q4v9qs 7wo52k 1e8r9u fdd3u2 7pc5ie j13nsu causal_hash_probe; do
        local final_count=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_id}.log")
        local base_count=$(grep -c "event=SEQUENCE_CHECK" "${CAUSAL_LOG_DIR}/${probe_id}.log" 2>/dev/null || echo "0")
        local expected=$((base_count + BURST_COUNT + RAPID_COUNT + INTERLEAVE_ROUNDS))
        
        if [[ "$final_count" == "$expected" ]]; then
            echo "✓ $probe_id: $final_count events (all increments accounted for)"
        else
            echo "✗ $probe_id: $final_count events, expected $expected"
        fi
    done
    
    echo ""
    echo "Next step: If all tests pass → Proceed to Phase 3: Replay Determinism"
}

main "$@"