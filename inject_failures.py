import threading
import time
import subprocess

def inject_gpu_pressure(duration=15):
    print("[inject-gpu] Starting compute task...", flush=True)
    try:
        cmd = "python3 -c \"import numpy as np; import time; a=np.random.rand(500,500); print('[gpu-start]'); for i in range(5): r=a@(a+1); time.sleep(1); print('[gpu-done]')\""
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=duration)
        print(result.stdout, flush=True)
    except subprocess.TimeoutExpired:
        print("[inject-gpu] GPU task timed out", flush=True)
    except Exception as e:
        print(f"[inject-gpu] Error: {e}", flush=True)

def inject_timeout(duration=10):
    print("[inject-timeout] Starting hanging operation...", flush=True)
    try:
        start = time.time()
        while time.time() - start < duration:
            time.sleep(1)
        print("[inject-timeout] Hanging operation completed", flush=True)
    except Exception as e:
        print(f"[inject-timeout] Timeout error: {e}", flush=True)

def inject_memory_pressure(duration=10):
    print("[inject-memory] Starting memory pressure...", flush=True)
    try:
        cmd = "python3 -c \"import time; import gc; for i in range(3): data=bytearray(100*1024*1024); del data; gc.collect(); time.sleep(1); print('[memory-done]')\""
        subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=duration)
    except subprocess.TimeoutExpired:
        print("[inject-memory] Memory task timed out", flush=True)
    except Exception as e:
        print(f"[inject-memory] Error: {e}", flush=True)

print("="*60)
print("INJECTING SIMULTANEOUS FAILURES")
print("="*60)

t1 = threading.Thread(target=inject_gpu_pressure, args=(20,), name="GPU")
t2 = threading.Thread(target=inject_timeout, args=(15,), name="TIMEOUT")
t3 = threading.Thread(target=inject_memory_pressure, args=(15,), name="MEMORY")

t1.start()
t2.start()
t3.start()

print("Threads started. Waiting for completion...", flush=True)

t1.join()
t2.join()
t3.join()

print("All failures injected. Monitoring recovery...", flush=True)
