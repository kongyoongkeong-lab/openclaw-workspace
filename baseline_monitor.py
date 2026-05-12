#!/usr/bin/env python3
"""
Pentagon Baseline Monitor v1.0
Tracks system quietness during idle operation (Phase 1)
No load triggers - pure observation mode
"""

import time
import json
import os
from pathlib import Path
from datetime import datetime

class PentagonBaselineMonitor:
    def __init__(self, output_dir=".openclaw/workspace/baseline"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots = []
        self.latency_samples = []
        
    def capture_snapshot(self):
        """Capture single system snapshot"""
        try:
            # GPU VRAM usage
            gpu_mem_info = Path("/proc/driver/nvidia/gpu_util/vram_usage")
            if gpu_mem_info.exists():
                with open(gpu_mem_info, "r") as f:
                    vram_lines = f.read().strip().split("\n")
                    vram_used = 0
                    for line in vram_lines:
                        if "vram" in line.lower() and "allocated" in line.lower():
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part.lower() == "vram" and i+1 < len(parts):
                                    try:
                                        vram_used = int(parts[i+1])
                                        break
                                    except:
                                        pass
            else:
                vram_used = 0
            
            # CPU load
            with open("/proc/loadavg") as f:
                load = list(map(float, f.readline().split()[:3]))
                cpu_baseline = load[1]  # 1-minute load
                
            # Event loop (approximate via process list)
            start = time.perf_counter()
            # Simple process check
            _ = os.listdir("/proc")
            event_delay = time.perf_counter() - start
            event_loop_delay = max(event_delay, 0.1)  # Normalize to ms
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "vram_used_mb": vram_used / 1024.0,
                "cpu_baseline": cpu_baseline,
                "event_loop_delay_ms": event_loop_delay * 1000,
                "process_count": len(os.listdir("/proc")),
                "quietness_score": 1.0 if event_loop_delay < 0.01 else 0.95  # Simplified metric
            }
            
            self.snapshots.append(snapshot)
            
            # Log to JSONL
            log_path = self.output_dir / "baseline.jsonl"
            with open(log_path, "a") as f:
                f.write(json.dumps(snapshot) + "\n")
                
            return snapshot
            
        except Exception as e:
            print(f"Snapshot error: {e}")
            return None
    
    def continuous_observation(self, duration_minutes=60, interval_seconds=30):
        """Run continuous baseline observation"""
        print(f"🔍 Baseline Observation Mode Started")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Interval: {interval_seconds}s")
        print(f"   Mode: NO LOAD TRIGGERS")
        print()
        
        interval = interval_seconds
        duration_seconds = duration_minutes * 60
        
        print(f"[{datetime.now().isoformat()}] Starting continuous observation...")
        print()
        
        start = time.time()
        
        while (time.time() - start) < duration_seconds:
            snapshot = self.capture_snapshot()
            if snapshot:
                print(f"[{snapshot['timestamp'][:26]}] VRAM: {snapshot['vram_used_mb']:.1f}MB | CPU: {snapshot['cpu_baseline']:.2f} | Event: {snapshot['event_loop_delay_ms']:.3f}ms | Quietness: {snapshot['quietness_score']}")
            
            time.sleep(interval)
        
        # Final snapshot
        snapshot = self.capture_snapshot()
        print(f"[{snapshot['timestamp'][:26]}] Final snapshot captured")
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate baseline analysis report"""
        if not self.snapshots:
            return None
        
        vram_values = [s['vram_used_mb'] for s in self.snapshots if 'vram_used_mb' in s]
        cpu_values = [s['cpu_baseline'] for s in self.snapshots if 'cpu_baseline' in s]
        event_values = [s['event_loop_delay_ms'] for s in self.snapshots if 'event_loop_delay_ms' in s]
        
        report = {
            "observation_period": {
                "start": self.snapshots[0]['timestamp'][:26],
                "end": self.snapshots[-1]['timestamp'][:26],
                "duration_seconds": (self.snapshots[-1]['timestamp'] - self.snapshots[0]['timestamp']).total_seconds() if hasattr(self.snapshots[0], 'timestamp') else 0
            },
            "latency": {
                "p50": sorted(event_values)[len(event_values)//2] if event_values else 0,
                "p95": sorted(event_values)[int(len(event_values)*0.95)] if event_values else 0
            },
            "resource_stability": {
                "vram_drift": max(vram_values) - min(vram_values) if vram_values else 0,
                "cpu_stability": max(cpu_values) - min(cpu_values) if cpu_values else 0
            },
            "runtime_behavior": {
                "max_event_delay": max(event_values) if event_values else 0,
                "avg_event_delay": sum(event_values)/len(event_values) if event_values else 0
            },
            "system_quietness": {
                "zero_latency_events": sum(1 for e in event_values if e < 0.1),
                "total_snapshots": len(self.snapshots)
            }
        }
        
        # Save report
        report_path = self.output_dir / "baseline_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "="*60)
        print("BASELINE SNAPSHOT GENERATED")
        print("="*60)
        print(f"Latency P50: {report['latency']['p50']:.2f}ms")
        print(f"Latency P95: {report['latency']['p95']:.2f}ms")
        print(f"VRAM Drift: {report['resource_stability']['vram_drift']:.2f}MB")
        print(f"CPU Stability: {report['resource_stability']['cpu_stability']:.2f}")
        print(f"Max Event Delay: {report['runtime_behavior']['max_event_delay']:.3f}ms")
        print(f"Avg Event Delay: {report['runtime_behavior']['avg_event_delay']:.3f}ms")
        print(f"System Quietness (Zero Latency Events): {report['system_quietness']['zero_latency_events']}/{report['system_quietness']['total_snapshots']}")
        print("="*60)
        
        return report


def main():
    monitor = PentagonBaselineMonitor()
    report = monitor.continuous_observation(duration_minutes=30, interval_seconds=30)  # 30 min baseline
    if report:
        print("\n✅ Baseline profiling complete.")
        print("   Report saved to:", monitor.output_dir / "baseline_report.json")
    else:
        print("\n⚠️  Baseline collection interrupted.")


if __name__ == "__main__":
    main()
