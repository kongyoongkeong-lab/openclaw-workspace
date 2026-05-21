# Tools: Delivery & Formatting

## 📡 Channel Tools
- `telegram_send(message, parse_mode)`: Send updates to Jason's mobile device.
- `slack_webhook(payload)`: Push system logs to the engineering channel.
- `local_notification(title, body)`: Trigger Windows/WSL2 desktop toasts.

## ✍️ Formatting Tools
- `markdown_to_pdf`: Convert research briefs into documents.
- `table_generator`: Transform JSON data arrays into readable Markdown tables.
- `latex_formatter`: Ensure complex formulas are correctly escaped for the UI.

## ⚙️ Optimization Rules
- **Streaming:** Use partial chunk delivery for Telegram to reduce perceived latency.
- **Batching:** Combine multiple small updates from @ops into a single "Status Report" to avoid spamming Jason.