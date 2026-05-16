#!/usr/bin/env python3
"""
Causal Probe #2: Shared Latent Structure Testing
-----------------------------------------------
Purpose: Test if true causal signals survive regime noise
Forbidden: No learning, no persistence, no telemetry storage
"""

import numpy as np
from scipy.stats import kendalltau


def compute_ranking_shift(metrics_a, metrics_b):
    """
    Compute Kendall's tau between two regime rankings.
    
    Higher |τ| = more regime-dependent (artifact)
    τ ≈ 0 = structurally stable (invariant)
    """
    ranks_a = np.argsort(metrics_a)
    ranks_b = np.argsort(metrics_b)
    
    tau, _ = kendalltau(ranks_a, ranks_b)
    return tau


def generate_shared_signal_with_noise(n_samples=1000, regime_type='normal'):
    """
    Generate metrics where causal signal is shared across regimes,
    but noise characteristics change.
    
    This tests: Can we distinguish true structure from regime artifact?
    """
    np.random.seed(42)
    
    # True causal signal (shared across all regimes)
    true_signal = np.random.normal(loc=0, scale=1, size=n_samples)
    
    # Regime-dependent noise
    if regime_type == 'normal':
        noise = np.random.normal(loc=0, scale=0.3, size=n_samples)
    elif regime_type == 'peak':
        noise = np.random.normal(loc=0, scale=1.0, size=n_samples)
    elif regime_type == 'recovery':
        noise = np.random.normal(loc=0, scale=0.6, size=n_samples)
    else:
        raise ValueError(f"Unknown regime type: {regime_type}")
    
    # Combined metric = true signal + regime noise
    metrics = true_signal + noise
    
    return metrics, true_signal


def run_invariance_test():
    """
    Execute structural invariance test with shared latent structure.
    """
    print("=" * 60)
    print("CAUSAL PROBE #2: SHARED LATENT STRUCTURE TESTING")
    print("=" * 60)
    
    # Generate metrics for each regime (with shared signal)
    metrics_normal, _ = generate_shared_signal_with_noise(regime_type='normal')
    metrics_peak, _ = generate_shared_signal_with_noise(regime_type='peak')
    metrics_recovery, _ = generate_shared_signal_with_noise(regime_type='recovery')
    
    print(f"\n📊 Regime Samples: {metrics_normal.shape[0]}")
    
    # Compute Kendall's tau matrix
    print("\n🔬 Computing ranking shifts...")
    
    tau_normal_peak = compute_ranking_shift(metrics_normal, metrics_peak)
    tau_normal_recovery = compute_ranking_shift(metrics_normal, metrics_recovery)
    tau_peak_recovery = compute_ranking_shift(metrics_peak, metrics_recovery)
    
    print(f"\n📈 Kendall's τ Matrix:")
    print("-" * 40)
    print(f"  Normal → Peak:      τ = {tau_normal_peak:.4f}")
    print(f"  Normal → Recovery:  τ = {tau_normal_recovery:.4f}")
    print(f"  Peak → Recovery:    τ = {tau_peak_recovery:.4f}")
    
    # Interpret results
    print("\n🧠 Causal Interpretation:")
    print("-" * 40)
    
    # Threshold for structural stability
    stability_threshold = 0.70  # Allow some regime dependency
    
    # Compute invariance flag
    invariance_flag = all(abs(tau) < stability_threshold for tau in [
        tau_normal_peak, tau_normal_recovery, tau_peak_recovery
    ])
    
    if invariance_flag:
        interpretation = "causal_candidate"
        print(f"✅ INVARIANCE: All τ < {stability_threshold}")
        print("📊 System preserves ordering across regimes")
        print("🎯 True causal structure is regime-stable")
    else:
        interpretation = "mixed"
        print(f"⚠️  PARTIAL INVARIANCE: Some τ > {stability_threshold}")
        print("📊 System shows partial regime dependency")
        print("🎯 Mixed: some causal signals stable, some noise-dominated")
    
    # Compute average magnitude
    avg_tau_magnitude = (abs(tau_normal_peak) + abs(tau_normal_recovery) + 
                        abs(tau_peak_recovery)) / 3
    
    print(f"\n📊 Average |τ| magnitude: {avg_tau_magnitude:.4f}")
    
    # Return structured result
    result = {
        "regimes": ["normal", "peak", "recovery"],
        "kendall_tau_matrix": [
            [1.0, tau_normal_peak, tau_normal_recovery],
            [tau_normal_peak, 1.0, tau_peak_recovery],
            [tau_normal_recovery, tau_peak_recovery, 1.0]
        ],
        "invariance_flag": invariance_flag,
        "interpretation": interpretation,
        "details": {
            "tau_normal_peak": tau_normal_peak,
            "tau_normal_recovery": tau_normal_recovery,
            "tau_peak_recovery": tau_peak_recovery,
            "avg_tau_magnitude": avg_tau_magnitude
        }
    }
    
    print("\n" + "=" * 60)
    print(f"RESULT: {interpretation.upper()}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    result = run_invariance_test()
    print(f"\n📋 Invariance flag: {result['invariance_flag']}")
    print(f"📋 Interpretation: {result['interpretation']}")
