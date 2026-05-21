# Bootstrap: @comms
**Sequence:** 03 (Delivery Layer)

## Boot Directives
- Verify Telegram bot connectivity.
- Initialize report templates (daily, weekly, alert).
- Check GitHub repo status for reports (`gh repo view --json name`).
- Test message delivery to configured channels (Telegram, Slack, etc.).

## Environment
- Set `REPORT_FREQUENCY=daily`
- Set `FORMAT_DEFAULT=markdown`
- Set `GITHUB_STATUS_IN_REPORTS=enabled`

## Report Templates

### Daily Pulse
```markdown
📊 **Pentagon Daily Pulse** — {date}
- Services: ✅ Gateway / ✅ Qdrant / ✅ Redis / ✅ ComfyUI
- GitHub: {commit_count} commits, {issue_count} open issues
- Last backup: {backup_tag}
- Health: 🟢 Stable
```

### Alert
```markdown
🚨 **Pentagon Alert** — {severity}
- Agent: {agent_id}
- Issue: {description}
- Check: {link or log path}
```

## Delivery Channels
| Channel | Status | Target |
|---------|--------|--------|
| Telegram | ⚙️ Configurable | Jason mobile |
| Webchat | ✅ Active | Current session |
| Slack | ⚙️ Configurable | Engineering channel |
