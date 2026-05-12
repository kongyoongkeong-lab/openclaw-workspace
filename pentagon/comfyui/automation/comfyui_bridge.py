#!/usr/bin/env python3
"""
Pentagon OpenClaw → ComfyUI Bridge
"""
import json
import subprocess
import time
import os

COMFY_BASE = "http://localhost:8188"
COMFY_PROMPT = f"{COMFY_BASE}/prompt"
COMFY_HISTORY = f"{COMFY_BASE}/history"
COMFY_QUEUE = f"{COMFY_BASE}/queue"
OUTPUT_DIR = os.path.expanduser("~/pentagon/comfyui/output")

def queue_workflow(workflow_path, prompt=None):
    """Queue generation via API."""
    with open(workflow_path) as f:
        data = json.load(f)
    
    # Add custom prompt if provided
    if prompt:
        # Find positive CLIPTextEncode node
        for node_id, node in data.items():
            if node.get("class_type") == "CLIPTextEncode":
                if "inputs" in node and "text" in node["inputs"]:
                    node["inputs"]["text"] = prompt
                break
    
    payload = {"prompt": data}
    response = subprocess.run(
        ["curl", "-X", "POST", COMFY_PROMPT, "-H", 
         "Content-Type: application/json", "-d", json.dumps(payload)],
        capture_output=True, text=True
    )
    
    print(response.stdout)
    return response.returncode == 0

def check_completion(timeout=300):
    """Wait for generation to complete."""
    start = time.time()
    while True:
        time.sleep(5)
        history = subprocess.run(
            ["curl", "-s", COMFY_HISTORY], capture_output=True, text=True
        )
        if "filename" in history.stdout:
            print("✅ Generation complete!")
            return True
        if time.time() - start > timeout:
            print("⏳ Timeout waiting for completion")
            return False

def get_latest_output():
    """Get latest PNG from output directory."""
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".png")]
    if files:
        return sorted(files)[-1]
    return None

if __name__ == "__main__":
    workflow = input("Workflow path: ").strip()
    prompt = input("Prompt (optional, press Enter for default): ").strip()
    
    if queue_workflow(workflow, prompt):
        print("✅ Queued successfully")
        if check_completion():
            print("🖼️  Latest output:", get_latest_output())
