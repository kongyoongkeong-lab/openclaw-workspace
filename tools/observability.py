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
import contextlib
import io
import tempfile
import base64
from urllib import request, error
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/home/jason2ykk/.openclaw/workspace"))
CONFIG_DIR = WORKSPACE / "config"
CONFIG_FILE = CONFIG_DIR / "observability.json"
LANGFUSE_URL = "http://localhost:3000"
MAIN_SESSIONS_FILE = Path.home() / ".openclaw" / "agents" / "main" / "sessions" / "sessions.json"

###############################################################################
# LangFuse API helpers (minimal, no SDK dependency needed for basic queries) #
###############################################################################

class LangFuseClient:
    """Minimal LangFuse API client using requests or urllib."""

    def __init__(self, public_key: str, secret_key: str, base_url: str = LANGFUSE_URL):
        self.public_key = public_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, data: dict = None):
        """Make an API request to LangFuse."""
        payload = json.dumps(data).encode("utf-8") if data else None
        headers = {
            "Authorization": f"Basic {self._basic_auth()}",
            "Content-Type": "application/json",
        }
        req = request.Request(
            f"{self.base_url}{path}",
            data=payload,
            headers=headers,
            method=method,
        )
        try:
            with request.urlopen(req, timeout=15) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8")
        except Exception as exc:
            return {"error": type(exc).__name__, "message": str(exc)}
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"error": "non_json_response", "status": "redacted"}

    def _basic_auth(self) -> str:
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


def mask_identifier(value: str, visible_prefix: int = 6, visible_suffix: int = 4) -> str:
    """Return a short non-secret fingerprint for key confirmation output."""
    if not value:
        return "<empty>"
    if len(value) <= visible_prefix + visible_suffix:
        return "<redacted>"
    return f"{value[:visible_prefix]}...{value[-visible_suffix:]}"


def stable_reference(value: str | None, prefix: str = "ref") -> str | None:
    """Return a stable non-reversible reference for local identifiers."""
    if value is None:
        return None
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def langfuse_credentials() -> tuple[str | None, str | None, str]:
    cfg = load_config()
    lf = cfg.get("langfuse", {})
    public_key = lf.get("public_key") or os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = lf.get("secret_key") or os.environ.get("LANGFUSE_SECRET_KEY")
    url = lf.get("url") or LANGFUSE_URL
    return public_key, secret_key, url


def sdk_client():
    public_key, secret_key, url = langfuse_credentials()
    if not public_key or not secret_key:
        raise RuntimeError("LangFuse API keys not configured. Run --init first.")
    try:
        from langfuse import Langfuse
    except Exception as exc:
        raise RuntimeError(f"LangFuse SDK unavailable: {exc}") from exc
    return Langfuse(public_key=public_key, secret_key=secret_key, host=url)


def session_rows(path: Path = MAIN_SESSIONS_FILE) -> dict[str, dict]:
    if not path.exists():
        raise RuntimeError(f"sessions file missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return {key: value for key, value in payload.items() if isinstance(value, dict)}
    if isinstance(payload, list):
        rows = {}
        for index, value in enumerate(payload):
            if isinstance(value, dict):
                rows[value.get("key") or value.get("sessionId") or str(index)] = value
        return rows
    raise RuntimeError(f"unsupported sessions format: {type(payload).__name__}")


def latest_session_with_usage(rows: dict[str, dict]) -> tuple[str, dict]:
    candidates = [
        (key, value) for key, value in rows.items()
        if isinstance(value.get("totalTokens"), int)
        or isinstance(value.get("inputTokens"), int)
        or isinstance(value.get("outputTokens"), int)
    ]
    if not candidates:
        raise RuntimeError("no session token counters found")
    return max(candidates, key=lambda item: int(item[1].get("updatedAt") or 0))


def usage_details_from_session(session: dict) -> dict[str, int]:
    mapping = {
        "input": "inputTokens",
        "output": "outputTokens",
        "cache_read": "cacheRead",
        "cache_write": "cacheWrite",
        "total": "totalTokens",
    }
    usage = {}
    for target, source in mapping.items():
        value = session.get(source)
        if isinstance(value, int):
            usage[target] = value
    if "total" not in usage:
        usage["total"] = sum(usage.values())
    return usage


def safe_session_metadata(key: str, session: dict) -> dict:
    return {
        "source": "openclaw-session-token-snapshot",
        "session_key": stable_reference(key, "session"),
        "session_id": stable_reference(session.get("sessionId"), "session_id"),
        "agent": key.split(":")[1] if key.startswith("agent:") and len(key.split(":")) > 1 else "unknown",
        "model": session.get("selectedModel") or session.get("configuredModel") or session.get("model"),
        "runtime": session.get("runtime"),
        "updated_at_ms": session.get("updatedAt"),
        "privacy": "token counters only; no prompt, output, user text, or credentials",
    }


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
     Password: stored in local password manager / private runtime notes
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
    print(f"🔑 Public key: {mask_identifier(public_key)}")
    print("🔑 Private credential: saved (value hidden)")
    print("Run `python3 tools/observability.py --init` to verify connection.")


def self_test() -> int:
    """Validate that key setup output never prints raw key values."""
    global CONFIG_DIR, CONFIG_FILE

    public_key = "public-test-value-123456"
    secret_key = "private-test-value-abcdef"
    original_config_dir = CONFIG_DIR
    original_config_file = CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmp:
        CONFIG_DIR = Path(tmp)
        CONFIG_FILE = CONFIG_DIR / "observability.json"
        captured = io.StringIO()
        try:
            with contextlib.redirect_stdout(captured):
                cmd_set_key(public_key, secret_key)
            output = captured.getvalue()
            if public_key in output or secret_key in output:
                print("self_test=fail reason=raw_key_in_output")
                return 1
            if not CONFIG_FILE.exists():
                print("self_test=fail reason=config_not_written")
                return 1
            usage = usage_details_from_session(
                {"inputTokens": 1, "outputTokens": 2, "cacheRead": 3, "cacheWrite": 4, "totalTokens": 10}
            )
            if usage != {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "total": 10}:
                print("self_test=fail reason=usage_details_mapping")
                return 1
            metadata = safe_session_metadata(
                "agent:main:test",
                {"sessionId": "s1", "selectedModel": "openai/test", "runtime": "test", "updatedAt": 1},
            )
            if "privacy" not in metadata or metadata.get("model") != "openai/test":
                print("self_test=fail reason=session_metadata")
                return 1
            if metadata.get("session_key") == "agent:main:test" or metadata.get("session_id") == "s1":
                print("self_test=fail reason=raw_session_identifier")
                return 1
        finally:
            CONFIG_DIR = original_config_dir
            CONFIG_FILE = original_config_file

    print("self_test=pass")
    return 0


def cmd_trace():
    """Run a quick test trace to verify observability pipeline."""
    client = sdk_client()
    trace_id = f"pentagon-test-{int(time.time())}"
    gen_id = f"gen-{trace_id}"

    print(f"📝 Creating test trace: {trace_id}")
    generation = client.start_observation(
        name="pentagon-observability-test",
        as_type="generation",
        input={"kind": "trace-smoke", "redacted": True},
        output={"ok": True},
        metadata={"source": "tools/observability.py", "privacy": "synthetic smoke test"},
        model="openai/gpt-5.5",
        usage_details={"input": 10, "output": 20, "total": 30},
    )
    generation.end()
    client.flush()
    print(f"   Generation: {gen_id}")
    print("   Usage: input=10 output=20 total=30")


def cmd_usage_snapshot(session_key: str | None = None):
    """Persist current OpenClaw session token counters as a LangFuse generation."""
    rows = session_rows()
    if session_key:
        if session_key not in rows:
            raise RuntimeError("session key not found")
        key, session = session_key, rows[session_key]
    else:
        key, session = latest_session_with_usage(rows)

    usage = usage_details_from_session(session)
    metadata = safe_session_metadata(key, session)
    model = metadata.get("model") or "unknown"
    client = sdk_client()
    generation = client.start_observation(
        name="openclaw-api-usage-snapshot",
        as_type="generation",
        input={"session_ref": stable_reference(key, "session"), "redacted": True},
        output={"usage_recorded": True},
        metadata=metadata,
        model=model,
        usage_details=usage,
    )
    generation.end()
    client.flush()
    print("usage_snapshot=sent")
    print(f"session_ref={stable_reference(key, 'session')}")
    print(f"model={model}")
    print(
        "usage="
        + ",".join(f"{name}={value}" for name, value in usage.items())
    )


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
    parser.add_argument("--usage-snapshot", action="store_true", help="Send current OpenClaw session token counters to LangFuse")
    parser.add_argument("--session-key", help="Specific OpenClaw session key for --usage-snapshot")
    parser.add_argument("--query", action="store_true", help="Query recent observability data")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic no-secret output checks")
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(self_test())
    elif args.init:
        cmd_init()
    elif args.set_key:
        cmd_set_key(args.set_key[0], args.set_key[1])
    elif args.trace:
        cmd_trace()
    elif args.usage_snapshot:
        cmd_usage_snapshot(args.session_key)
    elif args.query:
        cmd_query()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
