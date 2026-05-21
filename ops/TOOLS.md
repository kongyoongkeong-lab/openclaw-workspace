# Tools: System Interaction

- `delegate_task(agentId, task)`: Sends a natural language task to a sub-agent.

## 💻 Shell Tools
- `terminal_execute(command)`: Run bash/sh commands in the WSL2 environment.
- `docker_manager(action, container)`: Start, stop, or inspect Pentagon containers.

## 🐍 Scripting Tools
- `python_interpreter`: docker exec -i pentagon-runner python3 -c "{code}"
- `shell_execute`: docker exec -i pentagon-runner bash -c "{command}"
- `pip_install(package)`: Manage dependencies for custom agent skills.

## 📁 Filesystem Tools
- `fs_read/write/append`: Standard file manipulation in the project workspace.
- `git_manager`: Commit and push configuration changes to repos.

## 🐙 GitHub Tools
- `gh_repo_list`: List repos for kongyoongkeong-lab
- `gh_pr_create`: Create pull requests with title + body
- `gh_issue_list`: List open issues
- `gh_api(method, endpoint)`: Raw GitHub API access
- `git_push_with_tag`: Run `~/openclaw-stack/backup.sh` for daily backup

**Credentials:** `gh` auth via `~/.config/gh/hosts.yml` (PAT with `repo` + `workflow` scopes)

## ⚙️ Optimization Rules
- **Silent Mode:** Use `-q` or `> /dev/null` for verbose commands to keep logs clean unless debugging.
- **Cleanup:** Always remove temporary files (`/tmp/*`) after a task is finalized.
- **Git Hygiene:** Pull before push. Use `git pull --rebase` on stale remote.

