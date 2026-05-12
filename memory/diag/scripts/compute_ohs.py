#!/usr/bin/env python3
"""
OHS v1 Computation Module
Frozen constraints: Single-threaded, deterministic, no recursion, no adaptive scoring
"""

import sys

def compute_ohs(gaf, rpr, det, idle):
    """
    OHS formula: RPR*0.4 + (1-DETERMINISM)*0.1 + GAF*0.5
    Returns: OHS value and band classification
    """
    try:
        ohs = rpr * 0.4 + (1 - det) * 0.1 + gaf * 0.5
        if ohs >= 0.85:
            band = 'CRITICAL'
        elif ohs >= 0.65:
            band = 'DEGRADED'
        else:
            band = 'HEALTHY'
        return ohs, band
    except Exception:
        return None, 'UNKNOWN'

if __name__ == '__main__':
    # Parse arguments (or use defaults)
    if len(sys.argv) >= 5:
        gaf = float(sys.argv[1])
        rpr = float(sys.argv[2])
        det = float(sys.argv[3])
        idle = float(sys.argv[4])
    else:
        gaf, rpr, det, idle = 0.25, 0.09, 1.0, 30.0
    
    ohs, band = compute_ohs(gaf, rpr, det, idle)
    if ohs is not None:
        print(f'{ohs:.4f}|{band}|gaf={gaf:.2f}|rpr={rpr:.2f}|det={det:.2f}|idle={idle:.0f}%')
    else:
        print('Error computing OHS', file=sys.stderr)
