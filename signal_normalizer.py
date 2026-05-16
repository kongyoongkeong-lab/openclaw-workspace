#!/usr/bin/env python3
"""
signal_normalizer.py - Boring Canonicalization Layer

Principles:
1. Normalizer must remain boring
2. Never create information
3. Versioned output only
4. Fixed tables, no adaptive learning

Operations Allowed:
  - reorder fields
  - truncate strings/floats
  - normalize units
  - bucket with fixed tables
  - clamp with explicit ranges

Operations Forbidden:
  - infer meaning
  - interpret anomaly
  - explain values
  - aggregate causality
  - adapt buckets dynamically

Output Contract:
  {
    "schema_version": "signal-normalizer-v1",
    "signals": [...]
  }
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, asdict
from typing import Any, Literal


# ============================================================================
# FIXED TABLES (no adaptive learning)
# ============================================================================

VERSION = "signal-normalizer-v1"


# --------------------------------------------------------------------------
# CLAMP RANGES (explicit, no auto-adapt)
# --------------------------------------------------------------------------

def clamp_range(value: float, min_v: float, max_v: float) -> float:
    """Explicit range clamp. No auto-scale."""
    return max(min_v, min(max_v, value))


# --------------------------------------------------------------------------
# BUCKET TABLES (fixed, no adaptive percentile)
# --------------------------------------------------------------------------

# Latency buckets in milliseconds (fixed)
LATENCY_BUCKETS_MS: dict[int, tuple[int, int]] = {
    0: (0, 50),
    1: (50, 200),
    2: (200, 500),
    3: (500, 2000),
    4: (2000, float('inf')),
}


# Memory usage buckets (fixed percentages)
MEMORY_BUCKETS_PCT: dict[int, tuple[int, int]] = {
    0: (0, 20),
    1: (20, 50),
    2: (50, 70),
    3: (70, 90),
    4: (90, float('inf')),
}


# GPU utilization buckets (fixed percentages)
GPU_BUCKETS_PCT: dict[int, tuple[int, int]] = {
    0: (0, 30),
    1: (30, 60),
    2: (60, 85),
    3: (85, 100),
}


# CPU load buckets (fixed)
CPU_BUCKETS_PCT: dict[int, tuple[int, int]] = {
    0: (0, 20),
    1: (20, 50),
    2: (50, 70),
    3: (70, 95),
    4: (95, float('inf')),
}


# --------------------------------------------------------------------------
# UNIT NORMALIZATION
# --------------------------------------------------------------------------

def normalize_latency_ms(value: float | str) -> float:
    """Parse any latency representation to ms. No interpretation."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.endswith('ms'):
        return float(s[:-2])
    if s.endswith('s'):
        return float(s[:-1]) * 1000
    if s.endswith('µs'):
        return float(s[:-2]) / 1000
    # Assume ms if no unit
    try:
        return float(s)
    except ValueError:
        return 0.0


def normalize_memory_pct(value: float | str) -> float:
    """Parse any memory representation to percentage. No interpretation."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.endswith('%'):
        return float(s[:-1])
    try:
        return float(s)
    except ValueError:
        return 0.0


def normalize_bool(value: Any) -> bool | None:
    """Normalize boolean representations. No semantic inference."""
    if value is True or value is False:
        return value
    s = str(value).strip().lower()
    truthy = {'yes', 'true', '1', 'on', 'enabled'}
    falsy = {'no', 'false', '0', 'off', 'disabled'}
    if s in truthy:
        return True
    if s in falsy:
        return False
    return None


# ============================================================================
# CORE NORMALIZATION FUNCTION
# ============================================================================

@dataclass
class NormalizedSignal:
    """Canonical signal representation. No interpretation."""
    id: str
    schema_version: str
    timestamp_ns: int
    fields: dict[str, Any]
    bucket_map: dict[str, int]  # field_name -> bucket_index
    clamps: dict[str, float]    # field_name -> clamped_value


def normalize_string(value: str, max_length: int = 500) -> str:
    """Truncate and clean. No semantic extraction."""
    s = str(value).strip()
    # Remove trailing whitespace
    s = s.rstrip()
    # Truncate if too long
    if len(s) > max_length:
        s = s[:max_length] + '...'
    return s


def normalize_numeric(value: float, bucket_field: str | None, clamp_field: str | None) -> tuple[float, int | None, float | None]:
    """
    Normalize a numeric value:
      1. If bucket_field provided: assign fixed bucket
      2. If clamp_field provided: apply explicit clamp
    Returns: (normalized_value, bucket_index, clamped_value)
    """
    norm_value = value
    bucket_idx: int | None = None
    clamp_val: float | None = None

    # Bucket assignment (fixed table, no adaptive learning)
    if bucket_field is not None:
        # Try percentage buckets first
        if bucket_field == 'latency_bucket':
            # Latency already in ms
            bucket_idx = LATENCY_BUCKETS_MS.keys().__getitem__(0)
            for idx, (low, high) in LATENCY_BUCKETS_MS.items():
                if low <= value < high:
                    bucket_idx = idx
                    break
        elif bucket_field == 'memory_bucket':
            bucket_idx = MEMORY_BUCKETS_PCT.keys().__getitem__(0)
            for idx, (low, high) in MEMORY_BUCKETS_PCT.items():
                if low <= value < high:
                    bucket_idx = idx
                    break
        elif bucket_field == 'gpu_bucket':
            bucket_idx = GPU_BUCKETS_PCT.keys().__getitem__(0)
            for idx, (low, high) in GPU_BUCKETS_PCT.items():
                if low <= value < high:
                    bucket_idx = idx
                    break
        elif bucket_field == 'cpu_bucket':
            bucket_idx = CPU_BUCKETS_PCT.keys().__getitem__(0)
            for idx, (low, high) in CPU_BUCKETS_PCT.items():
                if low <= value < high:
                    bucket_idx = idx
                    break

    # Clamping (explicit ranges)
    if clamp_field is not None:
        if bucket_field == 'latency_bucket':
            clamp_val = clamp_range(value, 0.0, 10000.0)  # 10s max
        elif bucket_field == 'memory_bucket':
            clamp_val = clamp_range(value, 0.0, 100.0)
        elif bucket_field == 'gpu_bucket':
            clamp_val = clamp_range(value, 0.0, 100.0)
        elif bucket_field == 'cpu_bucket':
            clamp_val = clamp_range(value, 0.0, 100.0)
        else:
            clamp_val = value

    return norm_value, bucket_idx, clamp_val


def normalize_signal(raw: dict[str, Any], signal_id: str, timestamp_ns: int) -> NormalizedSignal:
    """
    Normalize a raw signal to canonical form.
    No inference. No interpretation. No causality aggregation.
    """
    fields: dict[str, Any] = {}
    bucket_map: dict[str, int] = {}
    clamps: dict[str, float] = {}

    # Extract and normalize fields (reorder to canonical form)
    # Canonical order: id, schema_version, timestamp_ns, <data_fields>, <metadata_fields>

    # 1. id (required)
    raw_id = raw.get('id')
    if raw_id is None:
        raw_id = signal_id  # fallback to provided id

    # 2. schema_version (fixed)
    fields['schema_version'] = VERSION

    # 3. timestamp_ns (normalize)
    raw_ts = raw.get('timestamp', raw.get('ts', raw.get('time')))
    if raw_ts is not None:
        if isinstance(raw_ts, (int, float)):
            fields['timestamp_ns'] = int(raw_ts * 1_000_000)  # convert to ns
        elif isinstance(raw_ts, str):
            # Parse ISO timestamp to ns (simple, no timezone inference)
            try:
                # Extract numeric part
                ts_str = str(raw_ts).split('T', 1)[-1].split('Z')[0]
                parts = ts_str.split(':')
                if len(parts) >= 3:
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2].split('.')[0])
                    fields['timestamp_ns'] = int((h * 3600 + m * 60 + s) * 1_000_000_000)
            except Exception:
                fields['timestamp_ns'] = int(raw_ts * 1_000_000)
        else:
            fields['timestamp_ns'] = int(raw_ts * 1_000_000)
    else:
        fields['timestamp_ns'] = timestamp_ns

    # 4. Normalize data fields (dumb transformations only)

    # Latency (if present)
    raw_latency = raw.get('latency_ms', raw.get('latency', raw.get('response_time')))
    if raw_latency is not None:
        norm_latency, latency_bucket, latency_clamp = normalize_numeric(
            normalize_latency_ms(raw_latency),
            bucket_field='latency_bucket',
            clamp_field='latency_clamp'
        )
        fields['latency_ms'] = norm_latency
        fields['latency_bucket'] = latency_bucket
        fields['latency_clamp'] = latency_clamp
        bucket_map['latency_bucket'] = latency_bucket or 0
        clamps['latency_clamp'] = latency_clamp or norm_latency

    # Memory (if present)
    raw_memory = raw.get('memory_pct', raw.get('memory', raw.get('ram_usage')))
    if raw_memory is not None:
        norm_mem, mem_bucket, mem_clamp = normalize_numeric(
            normalize_memory_pct(raw_memory),
            bucket_field='memory_bucket',
            clamp_field='memory_clamp'
        )
        fields['memory_pct'] = norm_mem
        fields['memory_bucket'] = mem_bucket
        fields['memory_clamp'] = mem_clamp
        bucket_map['memory_bucket'] = mem_bucket or 0
        clamps['memory_clamp'] = mem_clamp or norm_mem

    # GPU (if present)
    raw_gpu = raw.get('gpu_pct', raw.get('gpu', raw.get('vram_usage')))
    if raw_gpu is not None:
        norm_gpu, gpu_bucket, gpu_clamp = normalize_numeric(
            normalize_memory_pct(raw_gpu),
            bucket_field='gpu_bucket',
            clamp_field='gpu_clamp'
        )
        fields['gpu_pct'] = norm_gpu
        fields['gpu_bucket'] = gpu_bucket
        fields['gpu_clamp'] = gpu_clamp
        bucket_map['gpu_bucket'] = gpu_bucket or 0
        clamps['gpu_clamp'] = gpu_clamp or norm_gpu

    # CPU (if present)
    raw_cpu = raw.get('cpu_pct', raw.get('cpu', raw.get('load_average')))
    if raw_cpu is not None:
        norm_cpu, cpu_bucket, cpu_clamp = normalize_numeric(
            normalize_memory_pct(raw_cpu),
            bucket_field='cpu_bucket',
            clamp_field='cpu_clamp'
        )
        fields['cpu_pct'] = norm_cpu
        fields['cpu_bucket'] = cpu_bucket
        fields['cpu_clamp'] = cpu_clamp
        bucket_map['cpu_bucket'] = cpu_bucket or 0
        clamps['cpu_clamp'] = cpu_clamp or norm_cpu

    # 5. Normalize boolean flags (if present)
    raw_active = raw.get('is_active', raw.get('active', raw.get('running')))
    if raw_active is not None:
        fields['is_active'] = normalize_bool(raw_active)
        bucket_map['is_active'] = 0 if raw_active else -1
        bucket_map['is_active'] = 0 if raw_active else -1
        # bools don't get buckets in the same way, but we track them
        if raw_active:
            bucket_map['is_active'] = 0  # active = bucket 0 for convenience
        else:
            bucket_map['is_active'] = -1  # not active

    # 6. Normalize string fields (if present)
    raw_name = raw.get('name', raw.get('signal_name'))
    if raw_name is not None:
        fields['name'] = normalize_string(str(raw_name), max_length=200)

    raw_source = raw.get('source', raw.get('node'))
    if raw_source is not None:
        fields['source'] = normalize_string(str(raw_source), max_length=100)

    raw_type = raw.get('type', raw.get('category'))
    if raw_type is not None:
        fields['type'] = normalize_string(str(raw_type), max_length=100)

    # 7. Metadata fields (preserve as-is, no interpretation)
    raw_tags = raw.get('tags', raw.get('labels', raw.get('metadata')))
    if raw_tags is not None:
        if isinstance(raw_tags, str):
            fields['tags'] = normalize_string(raw_tags)
        elif isinstance(raw_tags, list):
            fields['tags'] = [normalize_string(t, max_length=50) for t in raw_tags]

    # 8. Any additional fields (passthrough, no interpretation)
    for key, val in raw.items():
        if key not in ('id', 'timestamp', 'ts', 'time', 'latency_ms', 'latency', 'response_time',
                       'memory_pct', 'memory', 'ram_usage', 'gpu_pct', 'gpu', 'vram_usage',
                       'cpu_pct', 'cpu', 'load_average', 'is_active', 'active', 'running',
                       'name', 'signal_name', 'source', 'node', 'type', 'category',
                       'tags', 'labels', 'metadata'):
            fields[key] = val

    return NormalizedSignal(
        id=str(raw_id),
        schema_version=VERSION,
        timestamp_ns=fields['timestamp_ns'],
        fields=fields,
        bucket_map=bucket_map,
        clamps=clamps
    )


def normalize_raw_input(raw_input: dict[str, Any], signal_id: str, timestamp_ns: int) -> dict[str, Any]:
    """
    Top-level normalizer entry point.
    Returns canonical JSON-serializable dict.
    """
    normalized = normalize_signal(raw_input, signal_id, timestamp_ns)
    return {
        'schema_version': normalized.schema_version,
        'signals': [asdict(normalized)]
    }


# ============================================================================
# CLI / STANDALONE USAGE
# ============================================================================

def main() -> None:
    """Example usage."""
    raw_signal = {
        'id': 'gpu-monitor-1',
        'gpu_pct': 87.3,
        'latency_ms': '1.2s',
        'memory_pct': '42%',
        'cpu_pct': 55,
        'active': True,
        'source': 'node-1',
        'timestamp': '2026-05-14T06:54:00Z',
        'tags': ['high-priority', 'gpu-intensive']
    }

    normalized = normalize_raw_input(raw_signal, 'gpu-monitor-1', 0)
    print(json.dumps(normalized, indent=2))


if __name__ == '__main__':
    main()
