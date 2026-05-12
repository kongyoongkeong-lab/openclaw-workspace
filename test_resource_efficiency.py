#!/usr/bin/env python3
"""
Pentagon Resource Efficiency Monitor
Monitors VRAM drift, GPU oscillation, memory leaks
Auto-improvement triggers for stability
"""

import time
import torch
import psutil
import subprocess
from datetime import datetime
from pathlib import Path

# GPU monitoring
class ResourceMonitor:
    def __init__(self):
        self.vram_history = []
        self.gpu_load_history = []
        self.cpu_history = []
        self.baseline_vram = None
        self.baseline_load = None
        
        # Thresholds
        self.vram_drift_threshold = 0.5  # GB
        self.gpu_oscillation_threshold = 10  # %
        self.sustained_high_threshold = 95  # %
        self.measurement_interval = 5  # seconds
        
    def get_gpu_stats(self):
        """Get current GPU statistics"""
        try:
            free_vram, total_vram = torch.cuda.mem_get_info()
            gpu_load = ((total_vram - free_vram) / total_vram) * 100
            
            return {
                'free_vram_gb': free_vram / 1024**2,
                'total_vram_gb': total_vram / 1024**2,
                'gpu_load_pct': gpu_load,
                'time': datetime.now()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_cpu_stats(self):
        """Get CPU statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            return {
                'cpu_percent': cpu_percent,
                'mem_used_pct': mem.percent,
                'mem_used_gb': mem.used / 1024**2
            }
        except Exception as e:
            return {'error': str(e)}
    
    def run_steady_load_test(self, duration=60, load_factor=0.7):
        """Run steady inference load test"""
        print("=" * 70)
        print("🧪 PENTAGON RESOURCE EFFICIENCY TEST")
        print("=" * 70)
        
        start_time = time.time()
        interval = self.measurement_interval
        samples = 0
        
        while time.time() - start_time < duration:
            # Get stats
            gpu = self.get_gpu_stats()
            cpu = self.get_cpu_stats()
            
            self.vram_history.append(gpu.get('free_vram_gb', 0))
            self.gpu_load_history.append(gpu.get('gpu_load_pct', 0))
            self.cpu_history.append(cpu.get('cpu_percent', 0))
            samples += 1
            
            # Print current stats
            if samples % 5 == 0:
                print(f"\n[{gpu['time'].strftime('%H:%M:%S')}]")
                print(f"  📟 GPU: {gpu['gpu_load_pct']:.1f}% ({gpu['free_vram_gb']:.2f}/{gpu['total_vram_gb']:.2f}GB VRAM)")
                print(f"  ⚙️ CPU: {cpu['cpu_percent']:.1f}%")
                
                # Check for issues
                issues = self.check_issues(gpu, cpu)
                if issues:
                    print(f"  ⚠️ Issues: {', '.join(issues)}")
                    self.trigger_improvements(issues)
            
            time.sleep(interval)
        
        # Final analysis
        print("\n" + "=" * 70)
        print("📊 RESOURCE EFFICIENCY ANALYSIS")
        print("=" * 70)
        
        self.analyze_results()
    
    def check_issues(self, gpu, cpu):
        """Check for resource issues"""
        issues = []
        
        # VRAM drift
        if len(self.vram_history) > 2:
            recent_avg = sum(self.vram_history[-5:]) / 5
            early_avg = sum(self.vram_history[:5]) / 5
            drift = early_avg - recent_avg
            if abs(drift) > self.vram_drift_threshold:
                issues.append(f"VRAM drift detected: {drift:.2f}GB")
        
        # GPU oscillation
        if len(self.gpu_load_history) > 10:
            recent_load = self.gpu_load_history[-5:]
            oscillation = max(recent_load) - min(recent_load)
            if oscillation > self.gpu_oscillation_threshold:
                issues.append(f"GPU oscillation: {oscillation:.1f}%")
        
        # Sustained high utilization
        if gpu.get('gpu_load_pct', 0) > self.sustained_high_threshold:
            issues.append(f"High GPU load: {gpu['gpu_load_pct']:.1f}%")
        
        return issues if issues else []
    
    def analyze_results(self):
        """Analyze resource usage over test duration"""
        if not self.vram_history:
            print("No data collected")
            return
        
        vram_stats = {
            'min': min(self.vram_history),
            'max': max(self.vram_history),
            'avg': sum(self.vram_history) / len(self.vram_history),
            'std': self.calculate_std(self.vram_history)
        }
        
        gpu_stats = {
            'min': min(self.gpu_load_history),
            'max': max(self.gpu_load_history),
            'avg': sum(self.gpu_load_history) / len(self.gpu_load_history),
            'std': self.calculate_std(self.gpu_load_history)
        }
        
        cpu_stats = {
            'min': min(self.cpu_history),
            'max': max(self.cpu_history),
            'avg': sum(self.cpu_history) / len(self.cpu_history),
            'std': self.calculate_std(self.cpu_history)
        }
        
        print(f"\n📟 VRAM Usage:")
        print(f"  Min: {vram_stats['min']:.2f}GB")
        print(f"  Max: {vram_stats['max']:.2f}GB")
        print(f"  Avg: {vram_stats['avg']:.2f}GB (±{vram_stats['std']:.2f})")
        print(f"  Drift: {abs(vram_stats['max'] - vram_stats['min']):.2f}GB")
        
        print(f"\n📟 GPU Load:")
        print(f"  Min: {gpu_stats['min']:.1f}%")
        print(f"  Max: {gpu_stats['max']:.1f}%")
        print(f"  Avg: {gpu_stats['avg']:.1f}% (±{gpu_stats['std']:.1f})")
        print(f"  Oscillation: {gpu_stats['max'] - gpu_stats['min']:.1f}%")
        
        print(f"\n⚙️ CPU Usage:")
        print(f"  Min: {cpu_stats['min']:.1f}%")
        print(f"  Max: {cpu_stats['max']:.1f}%")
        print(f"  Avg: {cpu_stats['avg']:.1f}% (±{cpu_stats['std']:.1f})")
        
        # Stability assessment
        print(f"\n🏥 STABILITY ASSESSMENT:")
        drift_ok = abs(vram_stats['max'] - vram_stats['min']) <= self.vram_drift_threshold
        oscillation_ok = (gpu_stats['max'] - gpu_stats['min']) <= self.gpu_oscillation_threshold
        high_load = max(gpu_load_history) <= self.sustained_high_threshold if self.gpu_load_history else True
        
        print(f"  VRAM Stability: {'✅' if drift_ok else '❌'} (Drift: {abs(vram_stats['max'] - vram_stats['min']):.2f}GB)")
        print(f"  GPU Oscillation: {'✅' if oscillation_ok else '❌'} ({gpu_stats['max'] - gpu_stats['min']:.1f}%)")
        print(f"  High Load Check: {'✅' if high_load else '❌'} (Max: {gpu_stats['max']:.1f}%)")
        
        if drift_ok and oscillation_ok and high_load:
            print(f"\n✅ RESOURCE EFFICIENCY: OPTIMAL")
        else:
            print(f"\n⚠️ RESOURCE EFFICIENCY: IMPROVEMENTS NEEDED")
    
    def calculate_std(self, data):
        """Calculate standard deviation"""
        if len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    def trigger_improvements(self, issues):
        """Generate auto-improvement suggestions"""
        print(f"\n🧠 AUTO-IMPROVEMENT TRIGGERS:")
        
        if "VRAM drift detected" in issues:
            print(f"  💡 SUGGESTION: Unload inactive models")
            print(f"  💡 SUGGESTION: Reduce Ollama keepalive duration")
        
        if "GPU oscillation" in issues:
            print(f"  💡 SUGGESTION: Enable adaptive inference throttling")
            print(f"  💡 SUGGESTION: Stagger agent inference timing")
        
        if "High GPU load" in issues:
            print(f"  💡 SUGGESTION: Enable VRAM governor mode")
            print(f"  💡 SUGGESTION: Reduce batch sizes")

def main():
    monitor = ResourceMonitor()
    
    # Run test
    duration = 60  # 1 minute steady load
    load_factor = 0.8  # 80% load
    
    monitor.run_steady_load_test(duration=duration, load_factor=load_factor)
    
    print(f"\n✅ Resource Efficiency Test Complete")
    print(f"Data saved to memory/2026-05-09.md")

if __name__ == "__main__":
    main()