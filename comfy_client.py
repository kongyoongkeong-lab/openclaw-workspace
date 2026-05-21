#!/usr/bin/env python3
"""
ComfyUI API Client — uses ComfyOrg API key for remote/workflow access.
Usage:
  python comfy_client.py workflow.json              # Queue a workflow
  python comfy_client.py --status <prompt_id>        # Check status
  python comfy_client.py --history <prompt_id>       # Get results
"""
import json
import os
import sys
import time
from urllib import request
from urllib.error import URLError

API_KEY = os.environ.get("COMFY_API_KEY", "")
BASE_URL = os.environ.get("COMFY_BASE_URL", "http://127.0.0.1:8188")

def queue_prompt(workflow_data):
    """Queue a workflow with API key attached."""
    payload = {"prompt": workflow_data}
    if API_KEY:
        payload["extra_data"] = {"api_key_comfy_org": API_KEY}
    
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(f"{BASE_URL}/prompt", data=data)
    try:
        resp = request.urlopen(req)
        return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        print(f"Error: {e.reason if hasattr(e, 'reason') else e}")
        sys.exit(1)

def get_status(prompt_id):
    """Check prompt status."""
    req = request.Request(f"{BASE_URL}/queue")
    resp = request.urlopen(req)
    return json.loads(resp.read().decode("utf-8"))

def get_history(prompt_id):
    """Get prompt history/output."""
    req = request.Request(f"{BASE_URL}/history/{prompt_id}")
    resp = request.urlopen(req)
    return json.loads(resp.read().decode("utf-8"))

def list_models():
    """List available checkpoints/models."""
    req = request.Request(f"{BASE_URL}/object_info/CheckpointLoaderSimple")
    resp = request.urlopen(req)
    return json.loads(resp.read().decode("utf-8"))

def system_stats():
    """Get system stats."""
    req = request.Request(f"{BASE_URL}/queue")
    resp = request.urlopen(req)
    return json.loads(resp.read().decode("utf-8"))

def test_connection():
    """Quick health check."""
    try:
        req = request.Request(f"{BASE_URL}/queue")
        resp = request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode("utf-8"))
        return {"status": "connected", "queue_running": len(data.get("queue_running", [])), "queue_pending": len(data.get("queue_pending", []))}
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--status":
        if len(sys.argv) < 3:
            print("Usage: comfy_client.py --status <prompt_id>")
            sys.exit(1)
        result = get_status(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "--history":
        if len(sys.argv) < 3:
            print("Usage: comfy_client.py --history <prompt_id>")
            sys.exit(1)
        result = get_history(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "--models":
        result = list_models()
        if "CheckpointLoaderSimple" in result:
            ckpts = result["CheckpointLoaderSimple"]["input"]["required"].get("ckpt_name", [])
            print(f"Available checkpoints ({len(ckpts)}):")
            for c in ckpts[:20]:
                print(f"  - {c}")
        else:
            print(json.dumps(result, indent=2)[:500])

    elif cmd == "--stats":
        print(json.dumps(system_stats(), indent=2))

    elif cmd == "--test":
        result = test_connection()
        if result["status"] == "connected":
            print(f"✅ Connected — running: {result['queue_running']}, pending: {result['queue_pending']}")
        else:
            print(f"❌ {result['error']}")
            sys.exit(1)

    elif cmd.endswith(".json"):
        with open(cmd, "r") as f:
            workflow = json.load(f)
        result = queue_prompt(workflow)
        print(json.dumps(result, indent=2))
        if "prompt_id" in result:
            print(f"\n✅ Prompt queued: {result['prompt_id']}")
            print(f"   Check status: python comfy_client.py --history {result['prompt_id']}")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

# === GitHub-tracked workflow helper ===
import glob

def list_workflows():
    """List all available workflow templates from the git-tracked directory."""
    wf_dir = os.path.expanduser("~/.openclaw/workspace/workflows")
    templates = glob.glob(os.path.join(wf_dir, "**/*.json"), recursive=True)
    if not templates:
        print("No workflow templates found. Export workflows to ~/.openclaw/workspace/workflows/")
        return
    print(f"\n📂 Workflow Templates ({len(templates)} found):")
    for t in sorted(templates):
        rel = os.path.relpath(t, wf_dir)
        size = os.path.getsize(t)
        print(f"  {rel}  ({size} bytes)")

def queue_with_prompt(workflow_path, prompt_text=None, prompt_node_id="6"):
    """Queue a workflow with an optional prompt override."""
    with open(workflow_path, "r") as f:
        workflow = json.load(f)
    
    # If it's an API format workflow, extract the inner workflow
    if "comfy_workflow" in workflow:
        wf = workflow["comfy_workflow"]
    else:
        wf = workflow
    
    # Override CLIPTextEncode node if prompt provided
    if prompt_text and prompt_node_id in wf:
        wf[prompt_node_id]["inputs"]["text"] = prompt_text
    
    return queue_prompt(wf)
