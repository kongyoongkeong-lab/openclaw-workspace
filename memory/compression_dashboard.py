#!/usr/bin/env python3
"""
Compression Monitoring Dashboard
Monitors LTM compression metrics and displays status.
"""

import json
from pathlib import Path
from datetime import datetime
import statistics

BASE_DIR = Path(__file__).parent
BASE_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts."""
    if not path.exists():
        return []
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def calculate_stats(records: list, field: str) -> dict:
    """Calculate statistics for a field across records."""
    if not records:
        return {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0}
    values = [r.get(field, 0) for r in records if isinstance(r.get(field), (int, float))]
    if not values:
        return {'count': len(records), 'mean': 0, 'std': 0, 'min': 0, 'max': 0}
    return {
        'count': len(values),
        'mean': statistics.mean(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values)
    }

def get_compression_summary() -> str:
    """Generate compression status report."""
    # Load episodic memory
    episodic_path = BASE_DIR / 'episodic.jsonl'
    episodic = load_jsonl(episodic_path)
    episodic_stats = calculate_stats(episodic, 'lines')
    
    # Load semantic memory
    semantic_path = BASE_DIR / 'semantic.jsonl'
    semantic = load_jsonl(semantic_path)
    semantic_stats = calculate_stats(semantic, 'lines')
    
    # Load agent logs
    agent_logs = []
    agents_dir = BASE_DIR / 'agents'
    if agents_dir.exists():
        for f in agents_dir.glob('*.jsonl'):
            agent_logs.extend(load_jsonl(f))
    agent_stats = calculate_stats(agent_logs, 'lines')
    
    # Load compression logs
    compress_path = BASE_DIR / 'compression.jsonl'
    compress = load_jsonl(compress_path)
    comp_stats = calculate_stats(compress, 'lines')
    
    # Calculate compression ratio
    total_lines = episodic_stats['count'] + semantic_stats['count']
    compressed_lines = compress_stats['count']
    compression_ratio = (compressed_lines / total_lines * 100) if total_lines > 0 else 0
    
    report = f"""
# 📊 LTM Compression Dashboard
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## 📈 Memory Pool Status

| Memory Type | Lines | Ratio |
|-------------|-------|-------|
| Episodic | {episodic_stats['count']} | - |
| Semantic | {semantic_stats['count']} | - |
| Compressed | {compressed_lines} | - |
| **Total** | **{total_lines}** | **{compression_ratio:.1f}%** |

## 📉 Compression Statistics

| Metric | Value |
|--------|-------|
| Compression Events | {compress_stats['count']} |
| Average Lines Compressed | {episodic_stats['mean'] if episodic_stats['count'] > 0 else 0:.0f} |
| Min Lines | {episodic_stats['min']:.0f} |
| Max Lines | {episodic_stats['max']:.0f} |

## 🟢 System Health

- **Threshold:** 3000 lines
- **Status:** {'⚠️ AT THRESHOLD' if total_lines >= 3000 else '✅ NOMINAL'}
- **Auto-Compression:** {'ACTIVE' if compress_stats['count'] > 0 else 'DISABLED'}

## 🔍 Agent Activity

- **Agents Monitored:** {len(agent_logs)} files
- **Total Agent Logs:** {agent_stats['count']} lines

---
*Dashboard v1.0 | LTM System*
"""
    return report

def check_threshold() -> dict:
    """Check if compression threshold has been reached."""
    episodic = load_jsonl(BASE_DIR / 'episodic.jsonl')
    threshold = 3000
    
    return {
        'current_lines': len(episodic),
        'threshold': threshold,
        'at_threshold': len(episodic) >= threshold,
        'headroom': max(0, threshold - len(episodic))
    }

if __name__ == '__main__':
    print(get_compression_summary())
    status = check_threshold()
    print(f"\n📌 Threshold Status: {status['at_threshold']} (Current: {status['current_lines']}/{status['threshold']})")
