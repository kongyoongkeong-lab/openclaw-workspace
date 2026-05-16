#!/usr/bin/env python3
"""
Causal Probe #1: Structural Invariance Testing
------------------------------------------------
Purpose: Test rank stability under regime perturbation
Forbidden: No learning, no persistence, no telemetry storage
"""

import numpy as np
from scipy.stats import kendalltau


def generate_regime_metrics(n_samples=1000, regime_type='normal'):
    """
    Generate metrics for a given regime.
    
    In a structurally stable system, ranking should be invariant.
    In a regime-artifact system, ranking flips with workload.
    
    This is a falsification probe - we test both hypotheses.
    """
    np.random.seed(42)
    
    if regime_type == 'normal':
        # Normal regime: baseline behavior
        metrics = np.random.normal(loc=0, scale=1, size=n_samples)
        
    elif regime_type == 'peak':
        # Peak regime: higher variance, potential ranking shift
        metrics = np.random.normal(loc=0.5, scale=1.5, size=n_samples)
        
    elif regime_type == 'recovery':
        # Recovery regime: intermediate behavior
        metrics = np.random.normal(loc=0.25, scale=1.2, size=n_samples)
        
    else:
        raise ValueError(f"Unknown regime type: {regime_type}")
    
    return metrics


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


def run_invariance_test():
    """
    Execute structural invariance test across 3 regimes.
    
    This is the first causal identifiability primitive.
    """
    print("=" * 60)
    print("CAUSAL PROBE #1: STRUCTURAL INVARIANCE TESTING")
    print("=" * 60)
    
    # Generate metrics for each regime
    metrics_normal = generate_regime_metrics(regime_type='normal')
    metrics_peak = generate_regime_metrics(regime_type='peak')
    metrics_recovery = generate_regime_metrics(regime_type='recovery')
    
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
    stability_threshold = 0.15
    
    # Compute invariance flag
    invariance_flag = all(abs(tau) < stability_threshold for tau in [
        tau_normal_peak, tau_normal_recovery, tau_peak_recovery
    ])
    
    if invariance_flag:
        interpretation = "causal_candidate"
        print(f"✅ INVARANCE: All τ < {stability_threshold}")
        print("📊 System is structurally stable")
        print("🎯 Rank ordering preserved across regimes")
    else:
        interpretation = "regime_artifact"
        print(f"⚠️  INSTABILITY: Some τ > {stability_threshold}")
        print("📊 System is regime-dependent")
        print("🎯 Rank ordering flips with workload")
    
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
