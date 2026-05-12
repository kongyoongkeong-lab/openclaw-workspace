#!/usr/bin/env python3
"""
Pentagon System Self-Repair Effectiveness Test Harness
Injects controlled faults and measures repair effectiveness metrics.
"""

import json
import time
import random
import threading
import psutil
import subprocess
from datetime import datetime
from pathlib import Path

# Test Configuration
TEST_DURATION = 300  # seconds
FAULT_TYPES = ["inference_timeout", "gpu_degradation", "model_disconnect", 
               "memory_corruption", "retrieval_starvation"]
FAULT_INJECTION_INTERVAL = 10  # seconds between fault injections
MTTR_THRESHOLD = 5  # seconds
RETRY_CEILING = 5
PROGRESSIVE_DEGRADATION_MODES = ["reduced_batch_size", "model_downgrade", 
                                   "fallback_to_small", "emergency_mode"]

class RepairTestHarness:
    def __init__(self):
        self.metrics = {
            "fault_injections": [],
            "recovery_attempts": [],
            "repair_successes": [],
            "mttr_samples": [],
            "retries_per_recovery": [],
            "repair_loop_detected": False,
            "oscillation_events": [],
            "degradation_quality_scores": []
        }
        self.active_fault = None
        self.fault_start_time = None
        self.repair_thread = None
        self.running = True
        self.repair_loop_counter = 0
        self.last_fault_type = None

    def inject_fault(self, fault_type, node=None):
        """Inject a controlled fault into the system"""
        fault_data = {
            "timestamp": datetime.now().isoformat(),
            "fault_type": fault_type,
            "injection_id": len(self.metrics["fault_injections"]) + 1,
            "recovery_start": None,
            "recovery_success": None,
            "mttr": None,
            "retries": 0,
            "fault_state": "INJECTED"
        }

        if fault_type == "inference_timeout":
            # Simulate inference timeout by killing a subprocess
            try:
                result = subprocess.run(
                    ["ollama", "run", "qwen3.5:9b", "echo test"],
                    timeout=2,  # Very short timeout to simulate fault
                    capture_output=True,
                    text=True
                )
                fault_data["simulated_error"] = "Inference timeout after 2s"
            except subprocess.TimeoutExpired:
                fault_data["simulated_error"] = "Simulated inference timeout"
                fault_data["fault_state"] = "SIMULATED"
        
        elif fault_type == "gpu_degradation":
            # Simulate GPU degradation by reducing performance
            try:
                result = subprocess.run(
                    ["nvidia-smi", "-i", "0", "-acm", "30", "--", 
                     "/usr/bin/nvidia-smi"],
                    capture_output=True,
                    text=True
                )
                fault_data["simulated_error"] = "GPU ACM reduced to 30%"
            except Exception as e:
                fault_data["simulated_error"] = f"GPU degradation: {str(e)}"
        
        elif fault_type == "model_disconnect":
            # Simulate model disconnect
            try:
                result = subprocess.run(
                    ["pkill", "-f", "ollama"],
                    capture_output=True,
                    text=True
                )
                fault_data["simulated_error"] = "Model disconnect signal sent"
                # Wait briefly then restart
                time.sleep(1)
                subprocess.run(["ollama", "serve"], capture_output=True)
                fault_data["auto_recovery"] = True
            except Exception as e:
                fault_data["simulated_error"] = f"Model disconnect: {str(e)}"
        
        elif fault_type == "memory_corruption":
            # Simulate memory corruption (create temp corrupt file)
            corrupt_file = Path("/tmp/corrupt_memory_test.tmp")
            try:
                corrupt_file.write_text("CORRUPTED_DATA_" + str(int(time.time())))
                fault_data["simulated_error"] = "Memory corruption simulated"
            except Exception as e:
                fault_data["simulated_error"] = f"Corruption attempt: {str(e)}"
        
        elif fault_type == "retrieval_starvation":
            # Simulate retrieval starvation
            try:
                Path("/tmp/.qdrant_busy.lock").write_text("LOCKED")
                fault_data["simulated_error"] = "Retrieval starvation (lock acquired)"
            except Exception as e:
                fault_data["simulated_error"] = f"Starvation simulation: {str(e)}"
        
        self.active_fault = fault_type
        self.fault_start_time = time.time()
        self.last_fault_type = fault_type
        self.metrics["fault_injections"].append(fault_data)
        
        print(f"[FAULT INJECTED] {fault_type.upper()} at {datetime.now().strftime('%H:%M:%S')}")
        return fault_data

    def monitor_and_recover(self):
        """Monitor system and attempt recovery when faults are active"""
        while self.running:
            try:
                if self.active_fault:
                    elapsed = time.time() - self.fault_start_time
                    
                    # Determine if fault should persist or be recovered
                    if elapsed > 15:  # Fault persists for 15 seconds then self-resolves
                        self.recover_fault(self.active_fault)
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(2)

    def recover_fault(self, fault_type):
        """Attempt recovery from active fault"""
        recovery_data = {
            "fault_type": fault_type,
            "fault_start_time": self.fault_start_time,
            "recovery_attempt_time": time.time(),
            "recovery_attempts": 0,
            "recovery_success": False,
            "recovery_time": None,
            "repair_method": None
        }
        
        recovery_start = time.time()
        max_retries = RETRY_CEILING
        
        for attempt in range(max_retries):
            recovery_data["recovery_attempts"] = attempt + 1
            
            print(f"[RECOVERY ATTEMPT {attempt+1}/{max_retries}] for {fault_type.upper()}")
            
            if fault_type == "inference_timeout":
                # Attempt: Restart inference service
                try:
                    subprocess.run(["ollama", "serve"], capture_output=True, timeout=5)
                    recovery_data["repair_method"] = "Restart inference service"
                except Exception as e:
                    recovery_data["error"] = str(e)
            
            elif fault_type == "gpu_degradation":
                # Attempt: Clear GPU ACM and restore performance
                try:
                    result = subprocess.run(
                        ["nvidia-smi", "-i", "0", "-acm", "100", "--", "true"],
                        capture_output=True,
                        text=True
                    )
                    recovery_data["repair_method"] = "Clear ACM, restore full performance"
                except Exception as e:
                    recovery_data["error"] = f"ACM clear failed: {e}"
                    # Progressive degradation: reduce batch size
                    if attempt == 0:
                        recovery_data["degradation_mode"] = "reduced_batch_size"
                        recovery_data["repair_method"] = "Applied reduced batch size"
                    
            elif fault_type == "model_disconnect":
                # Attempt: Reconnect model
                try:
                    subprocess.run(["ollama", "run", "qwen3.5:9b", "ping"], 
                                  capture_output=True, timeout=5)
                    recovery_data["repair_method"] = "Reconnect model service"
                except Exception as e:
                    recovery_data["error"] = f"Model reconnect failed: {e}"
                    if attempt == 0:
                        recovery_data["degradation_mode"] = "model_downgrade"
                        recovery_data["repair_method"] = "Switch to smaller model"
            
            elif fault_type == "memory_corruption":
                # Attempt: Clear corrupted file
                try:
                    corrupt_file = Path("/tmp/corrupt_memory_test.tmp")
                    corrupt_file.unlink(missing_ok=True)
                    recovery_data["repair_method"] = "Clear corrupted memory file"
                except Exception as e:
                    recovery_data["error"] = f"File cleanup failed: {e}"
                    
            elif fault_type == "retrieval_starvation":
                # Attempt: Clear retrieval lock
                try:
                    Path("/tmp/.qdrant_busy.lock").unlink(missing_ok=True)
                    recovery_data["repair_method"] = "Clear retrieval lock"
                except Exception as e:
                    recovery_data["error"] = f"Lock removal failed: {e}"
            
            # Check if recovery was successful
            try:
                # Quick health check
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                if result.returncode == 0:
                    recovery_data["recovery_success"] = True
                    recovery_data["recovery_time"] = (time.time() - recovery_start)
                    recovery_data["repair_oscillation"] = (
                        self.repair_loop_counter > 2 if hasattr(self, 'repair_loop_counter') else False
                    )
                    self.metrics["repair_successes"].append(recovery_data)
                    self.metrics["recovery_attempts"].append(recovery_data)
                    self.metrics["mttr_samples"].append({
                        "fault_type": fault_type,
                        "mttr": recovery_data["recovery_time"],
                        "recovery_attempts": recovery_data["recovery_attempts"]
                    })
                    self.metrics["retries_per_recovery"].append(recovery_data["recovery_attempts"])
                    
                    print(f"[RECOVERY SUCCESS] {fault_type.upper()} recovered in {recovery_data['recovery_time']:.2f}s")
                    
                    if recovery_data["repair_oscillation"]:
                        self.metrics["oscillation_events"].append({
                            "fault_type": fault_type,
                            "oscillation_detected": True
                        })
                    
                    self.active_fault = None
                    break
                else:
                    recovery_data["recovery_success"] = False
            
            except Exception as e:
                recovery_data["error"] = f"Health check failed: {e}"
                recovery_data["recovery_success"] = False
            
            # Progressive degradation escalation
            if recovery_data["recovery_success"] == False and attempt < max_retries - 1:
                if fault_type == "inference_timeout" and attempt == 1:
                    recovery_data["degradation_mode"] = "fallback_to_small"
                    recovery_data["repair_method"] = "Fallback to smaller model"
                elif fault_type == "gpu_degradation" and attempt == 1:
                    recovery_data["degradation_mode"] = "emergency_mode"
                    recovery_data["repair_method"] = "Emergency mode with reduced load"
            
            recovery_data["error"] = recovery_data.get("error", "Recovery failed")
            
            # Prevent repair oscillation
            if recovery_data["recovery_attempts"] >= 3:
                print(f"[REPAIR LOOP DETECTED] Multiple failures for {fault_type.upper()}")
                self.metrics["repair_loop_detected"] = True
                recovery_data["repair_loop_detected"] = True
                break
        
        recovery_data["fault_end_time"] = time.time()
        self.metrics["recovery_attempts"].append(recovery_data)
        
        # Clear active fault if successful
        if recovery_data.get("recovery_success"):
            self.active_fault = None
        
        return recovery_data

    def measure_degradation_quality(self, fault_type, recovery_data):
        """Measure how well the system degrades gracefully"""
        quality_score = 0.9  # Base score
        
        if fault_type == "inference_timeout" and recovery_data.get("degradation_mode"):
            # Check if degradation mode was applied
            if recovery_data.get("degradation_mode") == "reduced_batch_size":
                quality_score = 0.85
            elif recovery_data.get("degradation_mode") == "fallback_to_small":
                quality_score = 0.8
        elif fault_type == "gpu_degradation":
            if recovery_data.get("degradation_mode") == "emergency_mode":
                quality_score = 0.75
            else:
                quality_score = 0.9
        
        # Penalize if repair loop detected
        if self.metrics["repair_loop_detected"]:
            quality_score *= 0.9
        
        self.metrics["degradation_quality_scores"].append({
            "fault_type": fault_type,
            "quality_score": quality_score,
            "time_to_full_recovery": recovery_data.get("recovery_time", 0),
            "degradation_mode_applied": recovery_data.get("degradation_mode")
        })
        
        return quality_score

    def generate_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_id": "SELF-REPAIR-EFFECTIVENESS",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_faults_injected": len(self.metrics["fault_injections"]),
                "successful_repairs": len([f for f in self.metrics["fault_injections"] 
                                         if f.get("recovery_success")]),
                "failed_repairs": len([f for f in self.metrics["fault_injections"] 
                                      if not f.get("recovery_success")]),
                "avg_mttr": sum(self.metrics["mttr_samples"][i]["mttr"] 
                               for i in range(len(self.metrics["mttr_samples"])) 
                               if "mttr" in self.metrics["mttr_samples"][i]),
                "avg_retries": sum(self.metrics["retries_per_recovery"]) / 
                             len(self.metrics["retries_per_recovery"]) if self.metrics["retries_per_recovery"] else 0,
                "repair_loop_detected": self.metrics["repair_loop_detected"],
                "oscillation_events": len(self.metrics["oscillation_events"]),
                "avg_degradation_quality": sum(self.metrics["degradation_quality_scores"]) / 
                                         len(self.metrics["degradation_quality_scores"]) if self.metrics["degradation_quality_scores"] else 0
            },
            "faults_injection": self.metrics["fault_injections"],
            "recovery_attempts": self.metrics["recovery_attempts"],
            "mttr_samples": self.metrics["mttr_samples"],
            "retries_per_recovery": self.metrics["retries_per_recovery"],
            "repair_loops_detected": self.metrics["repair_loop_detected"],
            "oscillation_events": self.metrics["oscillation_events"],
            "degradation_quality_scores": self.metrics["degradation_quality_scores"],
            "recommendations": self._generate_recommendations()
        }
        
        return report

    def _generate_recommendations(self):
        """Generate auto-improvement recommendations based on observed metrics"""
        recommendations = []
        
        avg_mttr = self.metrics["mttr_samples"][i]["mttr"] for i in range(len(self.metrics["mttr_samples"])) if "mttr" in self.metrics["mttr_samples"][i]]
        if avg_mttr and avg_mttr > MTTR_THRESHOLD:
            recommendations.append({
                "category": "MTTR Optimization",
                "issue": f"Average MTTR ({avg_mttr:.2f}s) exceeds threshold ({MTTR_THRESHOLD}s)",
                "recommendation": "Implement staged recovery escalation with parallel recovery attempts",
                "priority": "HIGH"
            })
        
        if self.metrics["repair_loop_detected"]:
            recommendations.append({
                "category": "Repair Loop Prevention",
                "issue": "Repair loops detected during fault recovery",
                "recommendation": "Implement bounded retry ceilings and exponential backoff",
                "priority": "CRITICAL"
            })
        
        if self.metrics["oscillation_events"]:
            recommendations.append({
                "category": "Oscillation Prevention",
                "issue": f"{len(self.metrics['oscillation_events'])} oscillation events detected",
                "recommendation": "Add cooling period between recovery attempts",
                "priority": "MEDIUM"
            })
        
        avg_quality = sum(self.metrics["degradation_quality_scores"]) / len(self.metrics["degradation_quality_scores"]) if self.metrics["degradation_quality_scores"] else 1.0
        if avg_quality < 0.85:
            recommendations.append({
                "category": "Degradation Quality",
                "issue": f"Average degradation quality ({avg_quality:.2f}) below threshold (0.85)",
                "recommendation": "Implement progressive degradation modes with clearer state transitions",
                "priority": "HIGH"
            })
        
        if not recommendations:
            recommendations.append({
                "category": "System Health",
                "issue": "All repair metrics within acceptable thresholds",
                "recommendation": "Continue monitoring; consider increasing fault injection frequency",
                "priority": "LOW"
            })
        
        return recommendations

    def run_test(self):
        """Execute the full self-repair effectiveness test"""
        print("=" * 60)
        print("🧪 PENTAGON SYSTEM SELF-REPAIR EFFECTIVENESS TEST")
        print("=" * 60)
        print(f"Duration: {TEST_DURATION}s | Fault interval: {FAULT_INJECTION_INTERVAL}s")
        print(f"Fault types: {', '.join(FAULT_TYPES)}")
        print("-" * 60)
        
        start_time = time.time()
        fault_counter = 0
        
        while self.running and (time.time() - start_time) < TEST_DURATION:
            # Inject fault at regular intervals
            if fault_counter < len(FAULT_TYPES):
                fault_type = FAULT_TYPES[fault_counter % len(FAULT_TYPES)]
                self.inject_fault(fault_type)
                fault_counter += 1
            
            # Random fault injection (20% chance)
            if random.random() < 0.2:
                random_fault = random.choice([f for f in FAULT_TYPES if f != self.last_fault_type])
                self.inject_fault(random_fault)
            
            # Monitor and recover in background
            self.monitor_and_recover()
        
        self.running = False
        report = self.generate_report()
        print("\n" + "=" * 60)
        print("📊 TEST COMPLETE - GENERATING REPORT")
        print("=" * 60)
        
        # Print report
        print(json.dumps(report, indent=2, default=str))
        
        return report


if __name__ == "__main__":
    harness = RepairTestHarness()
    report = harness.run_test()
    
    # Save report
    Path("/home/jason2ykk/.openclaw/workspace/repair_test_results.json").write_text(
        json.dumps(report, indent=2, default=str)
    )
    
    print(f"\n📁 Results saved to: /home/jason2ykk/.openclaw/workspace/repair_test_results.json")
