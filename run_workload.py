import numpy as np
import json
import hashlib

# Task 1: Matrix multiplication 1000x1000 (seed=42)
np.random.seed(42)
A = np.random.rand(1000, 1000)
B = np.random.rand(1000, 1000)
C = np.dot(A, B)

# Task 2: Parse fixed JSON payload
json_payload = {
    "project": "p5-deterministic",
    "version": "1.0.0",
    "tasks": ["matrix_mult", "json_parse", "sum_integers"],
    "seed": 42,
    "status": "active"
}

# Task 3: Sum integers 1-1000
n = 1000
total_sum = n * (n + 1) // 2

# Task 4: Return results in canonical format
results = {
    "matrix_mult": {
        "shape": C.shape,
        "checksum_first_block": hashlib.md5(C[:10, :10].astype(np.int32).tobytes()).hexdigest()[:8],
        "checksum_final_block": hashlib.md5(C[-10:, -10:].astype(np.int32).tobytes()).hexdigest()[:8]
    },
    "json_parse": json_payload,
    "sum_integers": {
        "value": total_sum,
        "method": "formula"
    },
    "metadata": {
        "input_hash": hashlib.sha256(str(json_payload).encode()).hexdigest()[:12],
        "output_hash": hashlib.sha256(str(results).encode()).hexdigest()[:12]
    }
}

# Write to file for verification
output_path = "/home/jason2ykk/.openclaw/workspace/deterministic_workload_00a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print("Task complete. Output written to:", output_path)
print("Output hash (first 12 chars):", results["metadata"]["output_hash"])
