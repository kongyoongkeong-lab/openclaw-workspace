#!/usr/bin/env python3
"""
Pentagon Webhook Receiver — listens for GitHub events.
Starts on port 8090. Reacts to push, PR, and issue events.

Usage:
  python3 webhook_receiver.py           # Start server (foreground)
  python3 webhook_receiver.py --daemon  # Start in background
"""
import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
LOG_FILE = os.path.expanduser("~/openclaw_logs/webhook.log")

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        with open(LOG_FILE, "a") as f:
            f.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        event = self.headers.get("X-GitHub-Event", "unknown")
        delivery = self.headers.get("X-GitHub-Delivery", "unknown")
        payload = json.loads(body) if body else {}

        msg = f"📡 Webhook: {event} (delivery: {delivery[:8]}...)"
        print(msg)

        if event == "ping":
            print("  ✅ Ping received — webhook configured correctly")
        elif event == "push":
            self._handle_push(payload)
        elif event == "pull_request":
            self._handle_pr(payload)
        elif event == "issues":
            self._handle_issue(payload)
        elif event == "create":
            self._handle_create(payload)
        else:
            print(f"  ⏭️  Unhandled: {event}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def _handle_push(self, p):
        repo = p.get("repository", {}).get("full_name", "?")
        ref = p.get("ref", "?").replace("refs/heads/", "")
        author = p.get("head_commit", {}).get("author", {}).get("name", "?")
        commits = len(p.get("commits", []))
        print(f"  📦 {repo} ({ref}) — {commits} commits by {author}")
        if "openclaw-workspace" in repo:
            os.chdir(WORKSPACE)
            result = subprocess.run(["git", "pull", "--rebase"],
                                    capture_output=True, text=True)
            print(f"  {'✅ Synced' if result.returncode == 0 else '⚠️ Pull failed'}")

    def _handle_pr(self, p):
        action = p.get("action", "?")
        url = p.get("pull_request", {}).get("html_url", "?")
        title = p.get("pull_request", {}).get("title", "?")
        print(f"  🔍 PR {action}: {title}")
        print(f"     {url}")

    def _handle_issue(self, p):
        action = p.get("action", "?")
        title = p.get("issue", {}).get("title", "?")
        print(f"  📝 Issue {action}: {title}")

    def _handle_create(self, p):
        ref_type = p.get("ref_type", "?")
        ref = p.get("ref", "?")
        print(f"  🔖 Created {ref_type}: {ref}")

def start_server(port=8090):
    print(f"🔗 Pentagon Webhook Receiver — http://0.0.0.0:{port}")
    print(f"📝 Log: {LOG_FILE}")
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down")
        server.server_close()

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        pid = os.fork()
        if pid > 0:
            print(f"Webhook receiver started (PID: {pid})")
            sys.exit(0)
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()
    start_server()
