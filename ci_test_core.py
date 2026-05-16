import json
from runtime_snapshot_engine import build_snapshot

def load(file):
    with open(file, "r") as f:
        return json.load(f)

def test_determinism():
    trace = load("trace_sample.json")
    manifest = load("manifest.json")
    
    snap1 = build_snapshot(trace, manifest, "commit-A")
    snap2 = build_snapshot(trace, manifest, "commit-A")
    
    if snap1["behavioral_fingerprint"] == snap2["behavioral_fingerprint"]:
        print("✅ NO DRIFT")
    else:
        print("❌ DRIFT DETECTED")
        raise AssertionError("Behavioral fingerprint mismatch")

if __name__ == "__main__":
    test_determinism()
