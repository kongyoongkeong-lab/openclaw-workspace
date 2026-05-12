#!/usr/bin/env python3
"""
OHS v1 Calculator - Passive Telemetry Processor
No governance recursion, no adaptive scoring
"""

import json
import sys
from datetime import datetime, timezone

def calculate_ohs(gaf: float, rpr: float, determinism: float) -> float:
    """
    Compute OHS as a simple scalar heuristic.
    No adaptive thresholds, no recursive governance.
    """
    # Weighted average: RPR (0.4) + determinism_loss (0.1) + GAF (0.5)
    ohs = rpr * 0.4 + (1.0 - determinism) * 0.1 + gaf * 0.5
    return round(ohs, 2)

def classify_band(ohs: float) -> str:
    """
    Passive band classification.
    No autonomous actions based on this.
    """
    if ohs >= 0.85:
        return "CRITICAL"
    elif ohs >= 0.65:
        return "DEGRADED"
    else:
        return "HEALTHY"

def main():
    if len(sys.argv) < 4:
        print("Usage: ohs_calc.py <gaf> <rpr> <determinism>")
        sys.exit(1)

    gaf = float(sys.argv[1])
    rpr = float(sys.argv[2])
    det = float(sys.argv[3])

    ohs = calculate_ohs(gaf, rpr, det)
    band = classify_band(ohs)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trend_15m = 0.0  # Placeholder - requires external trend data

    record = {
        "schema_version": 1,
        "ts": ts,
        "ohs": ohs,
        "gaf": gaf,
        "rpr": rpr,
        "determinism": det,
        "trend_15m": trend_15m,
        "band": band
    }

    print(json.dumps(record))

if __name__ == "__main__":
    main()
