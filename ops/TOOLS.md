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
- `git_manager`: Commit and push configuration changes to Jason's repos.

## ⚙️ Optimization Rules
- **Silent Mode:** Use `-q` or `> /dev/null` for verbose commands to keep logs clean unless debugging.
- **Cleanup:** Always remove temporary files (`/tmp/*`) after a task is finalized.

# Tools: Operations
- `check_gpu`: /home/jason/check_gpu.sh
- `python_interpreter`: docker exec -i pentagon-runner python3 -c "{code}"

