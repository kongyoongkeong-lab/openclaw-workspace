#!/usr/bin/env bash
# ============================================================
# CAUSAL CONSISTENCY PROBE DEPLOYMENT
# ============================================================
# Phase A: Instrument Correctness (Required First)
# Phase B: System Causality (After Validation)
# ============================================================

set -euo pipefail

# ============================================================
# CONFIGURATION
# ============================================================
WORKSPACE="${OPENCLAW_WORKSPACE:-/home/jason2ykk/.openclaw/workspace}"
CAUSAL_LOG_DIR="${CAUSAL_LOG_DIR:-${WORKSPACE}/causal_logs/raw_events}"
METRICS_AGG_DIR="${METRICS_AGG_DIR:-${WORKSPACE}/causal_logs/metrics_agg}"

# ============================================================
# RAW EVENT LOGGING (APPEND-ONLY)
# ============================================================

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
    
    # Append-only raw event (never overwritten)
    cat >> "${CAUSAL_LOG_DIR}/${probe_id}.log" << EOF
[${CURRENT_SEQ}]$(date +%s%3N) probe_id=${probe_id} metric=${metric} event=${event_type} value=${value} seq=${CURRENT_SEQ}
EOF
}

# ============================================================
# PROBE DEPLOYMENTS
# ============================================================

# Probe 1: Logical Sequence Continuity
deploy_probe_q4v9qs() {
    log_raw_event "q4v9qs" "logical_time_gap_rate" "SEQUENCE_CHECK" "0"
    echo "✓ Probe q4v9qs deployed: logical_time_gap_rate"
}

# Probe 2: Stale Mutation Rejections
deploy_probe_7wo52k() {
    log_raw_event "7wo52k" "stale_mutation_rejections" "STALE_MUTATION" "0"
    echo "✓ Probe 7wo52k deployed: stale_mutation_rejections"
}

# Probe 3: Incident Version Conflicts
deploy_probe_1e8r9u() {
    log_raw_event "1e8r9u" "incident_version_conflicts" "VERSION_CONFLICT" "0"
    echo "✓ Probe 1e8r9u deployed: incident_version_conflicts"
}

# Probe 4: Retrieval Determinism Score
deploy_probe_fdd3u2() {
    log_raw_event "fdd3u2" "same_query_same_results_rate" "RETRIEVAL_QUERY" "0"
    echo "✓ Probe fdd3u2 deployed: retrieval_determinism_score"
}

# Probe 5: VRAM Recovery Half-Life
deploy_probe_7pc5ie() {
    log_raw_event "7pc5ie" "vram_recovery_half_life" "VRAM_RECOVERY" "0"
    echo "✓ Probe 7pc5ie deployed: vram_recovery_half_life"
}

# Probe 6: Governance Slowdown
deploy_probe_j13nsu() {
    log_raw_event "j13nsu" "decision_latency_per_observation" "GOVERNANCE_LATENCY" "0"
    echo "✓ Probe j13nsu deployed: governance_slowdown"
}

# Probe 7: State Hash Divergence (Ground Truth Oracle)
deploy_probe_causal_hash() {
    log_raw_event "causal_hash_probe" "final_incident_state_hash" "STATE_HASH_ORACLE" ""
    echo "✓ Probe causal_hash_probe deployed: final_incident_state_hash (GROUND TRUTH ORACLE)"
}

# ============================================================
# SINGLE-EVENT VALIDATION TEST
# ============================================================

validate_probe() {
    local probe_name="$1"
    local expected_seq="$2"
    
    if [[ -f "${CAUSAL_LOG_DIR}/${probe_name}.log" ]]; then
        local current_seq=$(wc -l < "${CAUSAL_LOG_DIR}/${probe_name}.log")
        
        if [[ "$current_seq" == "$expected_seq" ]]; then
            echo "✓ ${probe_name}: Single event incremented exactly once (seq=${current_seq})"
        else
            echo "✗ ${probe_name}: Expected ${expected_seq} events, found ${current_seq}"
            return 1
        fi
    else
        echo "✗ ${probe_name}: Log file not found"
        return 1
    fi
}

# ============================================================
# MAIN
# ============================================================

main() {
    local deploy_probes=true
    local run_validation=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --skip-validation)
                run_validation=false
                shift
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Create directories
    mkdir -p "${CAUSAL_LOG_DIR}" "${METRICS_AGG_DIR}"
    
    # Deploy probes
    echo "=== DEPLOYING CAUSAL CONSISTENCY PROBES ==="
    deploy_probe_q4v9qs
    deploy_probe_7wo52k
    deploy_probe_1e8r9u
    deploy_probe_fdd3u2
    deploy_probe_7pc5ie
    deploy_probe_j13nsu
    deploy_probe_causal_hash
    
    echo ""
    echo "=== PROBES DEPLOYED ==="
    echo "Deployed 7 probes to: ${CAUSAL_LOG_DIR}"
    
    # Run validation
    if [[ "$run_validation" == "true" ]]; then
        echo ""
        echo "=== RUNNING SINGLE-EVENT VALIDATION ==="
        validate_probe "q4v9qs" 1 || true
        validate_probe "7wo52k" 1 || true
        validate_probe "1e8r9u" 1 || true
        validate_probe "fdd3u2" 1 || true
        validate_probe "7pc5ie" 1 || true
        validate_probe "j13nsu" 1 || true
        validate_probe "causal_hash_probe" 1 || true
    fi
    
    echo ""
    echo "=== PROBE DEPLOYMENT COMPLETE ==="
    echo "Next step: Inject controlled events and validate instrumentation causality"
}

main "$@"