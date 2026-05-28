#!/usr/bin/env python3
"""
Observability Wrapper — LangFuse integration for Pentagon system.

Usage:
  python3 tools/observability.py --init       # Initialize LangFuse connection (run once)
  python3 tools/observability.py --trace "my_trace"   # Start a trace
  python3 tools/observability.py --query               # Query recent observations

Config file: /home/jason2ykk/.openclaw/workspace/config/observability.json
LangFuse UI: http://localhost:3000
"""

import json
import os
import sys
import hashlib
import hmac
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/home/jason2ykk/.openclaw/workspace"))
CONFIG_DIR = WORKSPACE / "config"
CONFIG_FILE = CONFIG_DIR / "observability.json"
LANGFUSE_URL = "http://localhost:3000"

###############################################################################
# LangFuse API helpers (minimal, no SDK dependency needed for basic queries) #
###############################################################################

class LangFuseClient:
    """Minimal LangFuse API client using requests or urllib."""

    def __init__(self, public_key: str, secret_key: str, base_url: str = LANGFUSE_URL):
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")
        self._auth = (public_key, secret_key)

    def _request(self, method: str, path: str, data: dict = None):
        """Make an API request to LangFuse."""
        import subprocess
        cmd = [
            "curl", "-s", "-u", f"{self.public_key}:{self.secret_key}",
            "-X", method, f"{self.base_url}{path}",
            "-H", "Content-Type: application/json",
        ]
        if data:
            cmd.extend(["-d", json.dumps(data)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": result.stdout, "stderr": result.stderr}

    def _basic_auth(self) -> str:
        import base64
        return base64.b64encode(f"{self.public_key}:{self.secret_key}".encode()).decode()

    def health(self) -> dict:
        return self._request("GET", "/api/public/health")

    def create_trace(self, trace_id: str, name: str = None, input_data: any = None, **kwargs) -> dict:
        payload = {"id": trace_id, "name": name or "unnamed", "input": input_data, **kwargs}
        return self._request("POST", "/api/public/traces", payload)

    def create_observation(self, trace_id: str, obs_id: str, obs_type: str = "GENERATION",
                           name: str = None, model: str = None, input_data: any = None,
                           output_data: any = None, usage: dict = None, **kwargs) -> dict:
        payload = {
            "id": obs_id,
            "traceId": trace_id,
            "type": obs_type,
            "name": name or "observation",
            "model": model,
            "input": input_data,
            "output": output_data,
            "usage": usage or {},
            **kwargs,
        }
        return self._request("POST", "/api/public/observations", payload)

    def query_traces(self, limit: int = 10, page: int = 1) -> dict:
        return self._request("GET", f"/api/public/traces?limit={limit}&page={page}")

    def query_generations(self, limit: int = 10) -> dict:
        return self._request("GET", f"/api/public/generations?limit={limit}")

    def get_project(self) -> dict:
        return self._request("GET", "/api/public/projects")


###############################################################################
# Config Management                                                          #
###############################################################################

def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"langfuse": {}}


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    print(f"✅ Config saved to {CONFIG_FILE}")


def cmd_init():
    """Initialize or verify LangFuse connection."""
    cfg = load_config()
    lf = cfg.get("langfuse", {})

    public_key = lf.get("public_key") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = lf.get("secret_key") or os.environ.get("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        print(f"""
⚠️  LangFuse API keys not configured.

Steps:
  1. Open http://localhost:3000 in your browser
  2. Sign in with:
     Email:    jason@langfuse.local
     Password: P3ntagon#2026!
  3. Navigate to Settings → API Keys
  4. Create a new API key (Project scope)
  5. Copy the Public Key and Secret Key here

Then run:
  python3 tools/observability.py --set-key <public_key> <secret_key>

Or set environment variables:
  export LANGFUSE_PUBLIC_KEY="pk-lf-..."
  export LANGFUSE_SECRET_KEY="sk-lf-..."
""")
        return

    print("🔍 Testing LangFuse connection...")
    client = LangFuseClient(public_key, secret_key)
    try:
        health = client.health()
        print(f"   Health: {health.get('status', '⚠️ check API key')}")
        project = client.get_project()
        data = project.get('data', [project])
        if isinstance(data, list) and data:
            p = data[0]
            print(f"   Project: {p.get('name', 'OK')} ({p.get('id', '?')})")
        elif 'id' in project:
            print(f"   Project: {project.get('name', 'OK')} ({project['id']})")
        else:
            msg = project.get('message') or list(project.keys())[0] if project else 'unknown'
            print(f"   Auth: {'OK' if 'data' in project else msg}")
        print(f"\n✅ LangFuse ready at {LANGFUSE_URL}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


def cmd_set_key(public_key: str, secret_key: str):
    """Save LangFuse API keys to config."""
    cfg = load_config()
    cfg["langfuse"] = {
        "public_key": public_key,
        "secret_key": secret_key,
        "url": LANGFUSE_URL,
        "updated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
    }
    save_config(cfg)
    print(f"🔑 Public key: {public_key}")
    print(f"🔑 Secret key: {secret_key[:8]}...{secret_key[-4:]}")
    print("Run `python3 tools/observability.py --init` to verify connection.")


def cmd_trace():
    """Run a quick test trace to verify observability pipeline."""
    cfg = load_config()
    lf = cfg.get("langfuse", {})
    pk = lf.get("public_key") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = lf.get("secret_key") or os.environ.get("LANGFUSE_SECRET_KEY")

    if not pk or not sk:
        print("❌ API keys not configured. Run --init first.")
        return

    client = LangFuseClient(pk, sk)
    trace_id = f"pentagon-test-{int(time.time())}"
    gen_id = f"gen-{trace_id}"

    print(f"📝 Creating test trace: {trace_id}")
    
    # Create a trace
    result = client.create_trace(trace_id, name="pentagon-observability-test",
                                  input_data="Testing LangFuse integration")
    tid = result.get("id") or result.get("message", "⚠️")
    print(f"   Trace: {tid}")

    # Create a generation observation
    result = client.create_observation(trace_id, gen_id, obs_type="GENERATION",
                                        name="test-generation", model="deepseek/deepseek-v4-flash",
                                        input_data="test input", output_data="test output",
                                        usage={"input": 10, "output": 20, "total": 30})
    gid = result.get("id") or result.get("message", "⚠️")
    print(f"   Generation: {gid}")

    # Query traces
    traces = client.query_traces(limit=5)
    print(f"\n📊 Recent traces: {len(traces.get('data', []))}")


def cmd_query():
    """Query recent observability data."""
    cfg = load_config()
    lf = cfg.get("langfuse", {})
    pk = lf.get("public_key") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    sk = lf.get("secret_key") or os.environ.get("LANGFUSE_SECRET_KEY")

    if not pk or not sk:
        print("❌ API keys not configured. Run --init first.")
        return

    client = LangFuseClient(pk, sk)

    print("📊 Last 10 traces:")
    traces = client.query_traces(limit=10)
    for t in traces.get("data", []):
        ts = t.get("timestamp", "")[:19]
        print(f"  [{ts}] {t.get('name', '-')}  id={t.get('id', '?')[:20]}")

    print("\n📊 Last 10 generations:")
    gens = client.query_generations(limit=10)
    for g in gens.get("data", []):
        print(f"  model={g.get('model', '-')}  tokens={g.get('usage',{}).get('totalTokens', '?')}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pentagon Observability Tool")
    parser.add_argument("--init", action="store_true", help="Initialize/test LangFuse connection")
    parser.add_argument("--set-key", nargs=2, metavar=("PUBLIC_KEY", "SECRET_KEY"), help="Set LangFuse API keys")
    parser.add_argument("--trace", action="store_true", help="Run a test trace")
    parser.add_argument("--query", action="store_true", help="Query recent observability data")
    args = parser.parse_args()

    if args.init:
        cmd_init()
    elif args.set_key:
        cmd_set_key(args.set_key[0], args.set_key[1])
    elif args.trace:
        cmd_trace()
    elif args.query:
        cmd_query()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
