import json
import subprocess
import time

def run_test_with_seed(seed):
    """Run test with specific seed for reproducibility"""
    # Simulate a workload that might vary based on seed
    result = {
        "seed": seed,
        "timestamp": time.time(),
        "output": f"Test output for seed {seed}"
    }
    return result

# Run 5 parallel-ish tests
seeds = [42, 123, 456, 789, 101112]
print("Running parallel tests with different seeds...\n")

results = []
for i, seed in enumerate(seeds, 1):
    print(f"Starting test {i} (seed={seed})")
    start = time.time()
    # Small delay to simulate varying workloads
    time.sleep(0.01)
    results.append(run_test_with_seed(seed))
    print(f"Completed test {i} in {time.time()-start:.4f}s")

print("\n=== Results Summary ===")
for r in results:
    print(json.dumps(r, indent=2))
