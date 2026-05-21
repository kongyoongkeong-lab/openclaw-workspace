# Tools: Delivery & Formatting

## 📡 Channel Tools
- `telegram_send(message, parse_mode)`: Send updates to Jason's mobile device (pair-mode).
- `telegram_pair(user_id)`: Initiate pairing flow for new Telegram users.
- `telegram_broadcast(message)`: Send to all paired Telegram users.
- `slack_webhook(payload)`: Push system logs to engineering channel.
- `local_notification(title, body)`: Trigger Windows/WSL2 desktop toasts.

## 🐙 GitHub Channel Tools
- `gh_issue_create(title, body, label)`: Create GitHub issue as notification.
- `gh_issue_list(label)`: List recent issues by label (notification/incident).
- `gh_repo_status()`: Get commit count, open issues, last backup tag.

## ✍️ Formatting Tools
- `markdown_to_pdf`: Convert research briefs into documents.
- `table_generator`: Transform JSON data arrays into readable Markdown tables.
- `latex_formatter`: Ensure complex formulas are correctly escaped for the UI.
- `report_templater(template, data)`: Fill in report templates with live data.

## 📋 Report Templates (from CHANNEL_PROTOCOL.md)
1. **Daily Pulse** — `comms/BOOTSTRAP.md` has template
2. **Alert** — Status + Severity + Action
3. **Task Complete** — Agent + Summary + Latency

## ⚙️ Optimization Rules
- **Streaming:** Use partial chunk delivery for Telegram to reduce perceived latency.
- **Batching:** Combine multiple small updates from @ops into a single "Status Report" to avoid spamming Jason.
- **GitHub Issues:** Only create for failures that survive 2 auto-recovery attempts.
- **Deduplication:** Check `gh issue list` before creating duplicate notifications.
