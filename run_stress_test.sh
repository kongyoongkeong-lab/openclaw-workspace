#!/bin/bash
echo "🚀 STARTING FAILURE INJECTION TEST"
echo "======================================"

# Function to inject GPU pressure
inject_gpu() {
    echo "[gpu] Injecting GPU pressure..."
    python3 -c "import numpy as np; import time; a=np.random.rand(500,500); for i in range(5): r=a@(a+1); time.sleep(1); print('[gpu] done')"
}

# Function to inject timeout
inject_timeout() {
    echo "[timeout] Injecting timeout..."
    sleep 15
    echo "[timeout] done"
}

# Function to inject memory pressure
inject_memory() {
    echo "[memory] Injecting memory pressure..."
    import subprocess; subprocess.run("python3 -c \"import gc; for i in range(3): data=bytearray(100*1024*1024); del data; gc.collect(); print('[memory] done')\"", shell=True)
}

# Run all in parallel
inject_gpu &
inject_timeout &
inject_memory &

wait
echo "======================================"
echo "✅ FAILURES INJECTED AND TEST COMPLETE"
