# Tools: Monitoring & Enforcement

## 🛡 Security Tools
- `command_scanner(cmd)`: Regex-based pattern matching for dangerous bash syntax.
- `pii_scrubber(text)`: Automatically masks strings that look like API keys or passwords.
- `git_secret_scanner()`: Check staged git diff for credential patterns (`ghp_`, `gho_`, `sk-`, `comfyui-`, `api_key`).
- `github_actions_scan()`: Review workflow files for insecure permissions.

## 📊 Monitoring Tools
- `wsl_top()`: Monitor CPU and RAM usage within the Ubuntu container.
- `heartbeat_check()`: Ping @main, @intel, and @ops to ensure all services are responsive.

## ⚙️ Enforcement Rules
- **Kill Switch:** Authorized to issue `docker restart` commands if a container stops responding.
- **Intercept:** Automatically stop any output containing the string `b218f61b67...` (System Token).
