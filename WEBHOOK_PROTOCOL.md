# 🔗 Webhook Protocol — v1

**Owner:** @ops (Executor) + @comms (Delivery)
**Scope:** GitHub → Pentagon → Slack
**Updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Architecture

```
GitHub Events (push, PR, issues)
      │
      ▼
┌─────────────────────┐
│  GitHub Webhook      │ → POST to receiver endpoint
│  (config per repo)   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Webhook Receiver    │ → Parse event → Route to agent
│  (script/service)    │
└─────────┬───────────┘
          │
          ├── @intel    → New issue: research context
          ├── @ops      → Push event: deploy/backup
          ├── @sentinel → PR event: security review
          └── @comms    → Format + deliver notification
```

## GitHub Webhook Configuration

### Add Webhook to Repos

```bash
# For openclaw-workspace
gh api repos/kongyoongkeong-lab/openclaw-workspace/hooks \
  --method POST \
  -f name="web" \
  -f active=true \
  -f events='["push", "pull_request", "issues", "create"]' \
  -f config='{"url":"http://localhost:8090/webhook","content_type":"json","secret":"<webhook_secret>"}'

# For openclaw-config
gh api repos/kongyoongkeong-lab/openclaw-config/hooks \
  --method POST \
  -f name="web" \
  -f active=true \
  -f events='["push"]' \
  -f config='{"url":"http://localhost:8090/webhook","content_type":"json","secret":"<webhook_secret>"}'
```

### Event Types to Track

| Event | Trigger | Action |
|-------|---------|--------|
| `push` | Code pushed | @ops: sync workspace, verify backup |
| `pull_request` | PR opened/updated | @sentinel: review diff for secrets |
| `issues` | Issue created | @intel: research issue context |
| `create` | Branch/tag created | @ops: log new branch |

## Webhook Receiver (Python)

```python
#!/usr/bin/env python3
"""Pentagon webhook receiver — listens for GitHub events."""
import json
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        event = self.headers.get("X-GitHub-Event", "unknown")
        payload = json.loads(body) if body else {}

        print(f"📡 Webhook received: {event}")

        if event == "push":
            self.handle_push(payload)
        elif event == "pull_request":
            self.handle_pr(payload)
        elif event == "issues":
            self.handle_issue(payload)
        else:
            print(f"  ⏭️  Unhandled event: {event}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def handle_push(self, payload):
        repo = payload.get("repository", {}).get("full_name", "unknown")
        ref = payload.get("ref", "unknown")
        # Auto-pull if it's our workspace
        if "openclaw-workspace" in repo:
            os.chdir(WORKSPACE)
            subprocess.run(["git", "pull", "--rebase"], capture_output=True)
            print(f"  ✅ Synced {repo} ({ref})")

    def handle_pr(self, payload):
        action = payload.get("action", "unknown")
        pr_url = payload.get("pull_request", {}).get("html_url", "")
        print(f"  🔍 PR {action}: {pr_url}")
        # @sentinel should review PRs

    def handle_issue(self, payload):
        action = payload.get("action", "unknown")
        title = payload.get("issue", {}).get("title", "")
        print(f"  📝 Issue {action}: {title}")

def start_server(port=8090):
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"🔗 Webhook receiver running on :{port}")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
```

## Slack Notification Format

When @comms receives a webhook event:

```markdown
📡 **GitHub Event** — {event_type}
- **Repo:** {repo}
- **Branch:** {branch}
- **Author:** {author}
- **Action:** {description}
- **Link:** {url}
```


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.

## Files

| File | Purpose |
|------|---------|
| `~/.openclaw/workspace/WEBHOOK_PROTOCOL.md` | This document |
| `~/.openclaw/workspace/webhook_receiver.py` | Event receiver script |
| `~/.openclaw/workspace/.github/workflows/webhook-test.yml` | Test workflow |
