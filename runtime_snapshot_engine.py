import hashlib
import json
import uuid


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_list(items):
    return sha256("|".join(sorted(items)))


def build_snapshot(runtime_trace, manifest, git_commit):
    """
    Minimal behavioral snapshot generator (v0)
    """
    # ---- topology layer ----
    workflow_nodes = runtime_trace.get("workflow_nodes", [])
    agents = runtime_trace.get("agents", [])

    topology_hash = hash_list(workflow_nodes + agents)

    # ---- execution signature ----
    tool_calls = runtime_trace.get("tool_calls", [])
    latencies = runtime_trace.get("latencies", [])

    tool_pattern_hash = hash_list([t["tool"] for t in tool_calls])

    latency_buckets = [
        str(int(l // 100) * 100) for l in latencies
    ]
    latency_profile_hash = hash_list(latency_buckets)

    # ---- behavioral fingerprint ----
    combined = topology_hash + tool_pattern_hash + latency_profile_hash
    behavioral_fingerprint = sha256(combined)

    return {
        "snapshot_id": str(uuid.uuid4()),
        "binding": {
            "git_commit": git_commit,
            "manifest_version": manifest.get("version", "unknown")
        },
        "topology": {
            "hash": topology_hash,
            "nodes": len(workflow_nodes),
            "agents": len(agents)
        },
        "execution_signature": {
            "tool_pattern_hash": tool_pattern_hash,
            "latency_profile_hash": latency_profile_hash
        },
        "behavioral_fingerprint": behavioral_fingerprint
    }


def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Runtime Snapshot Engine v0")
    parser.add_argument("--trace", type=str, help="Path to runtime trace JSON")
    parser.add_argument("--manifest", type=str, help="Path to manifest JSON")
    parser.add_argument("--git-commit", type=str, help="Git commit hash")
    parser.add_argument("--output", type=str, help="Path to output snapshot JSON")
    args = parser.parse_args()

    with open(args.trace, "r") as f:
        runtime_trace = json.load(f)

    with open(args.manifest, "r") as f:
        manifest = json.load(f)

    snapshot = build_snapshot(runtime_trace, manifest, args.git_commit)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(snapshot, f, indent=2)
            print(f"Snapshot written to: {args.output}")
    else:
        print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
