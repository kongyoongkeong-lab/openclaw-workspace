# OpenClaw 快捷指令注册表

来源：根据 Jason 2026-05-22 提供的快捷指令列表、当前 workspace 已实现工具、以及 GitHub 远端资料审计后重建。

原则：

- 本文件是快捷指令的本地 source of truth。
- GitHub 只作为咨询和版本对照来源，不从旧备份自动恢复。
- 涉及 token、账号、备份、生产服务、Qdrant 写入、长期任务的指令必须保留安全确认或脱敏输出。
- `状态=已接入` 表示当前 workspace 有明确执行路径；`状态=待接入` 表示保留入口，但后端脚本/流程需要恢复或重建。

| 指令 | 别名 | 功能 | 执行路径 / 处理方式 | 状态 | 安全规则 |
|---|---|---|---|---|---|
| `指令列表` | - | 显示所有快捷指令 | 读取 `shortcuts.md` | 已接入 | 只读 |
| `今日新闻` | `每日新闻`, `daily news` | 生成每日新闻，优先使用 6 小时内缓存 | 按 `MEMORY.md` / `AGENTS.md` 的 daily news workflow；缺少 `daily_news.md` 时需先重建工作流 | 待接入 | 搜索来源需可追溯；不刷新除非 Jason 明确要求 |
| `刷新新闻` | `重新抓取`, `重新生成今日新闻`, `deep search`, `深度搜索` | 强制刷新每日新闻缓存 | daily news workflow 的刷新模式 | 待接入 | 明确刷新才联网重抓 |
| `今日AI` | `今日 AI`, `AI日报`, `最新AI动态` | 生成最近 7 天 AI 日报 | 按 `MEMORY.md` / `AGENTS.md` 的 AI daily workflow；缺少 `daily_ai.md` 时需先重建工作流 | 待接入 | 需标注日期和来源 |
| `额度查询` | - | 查询 ChatGPT Plus / OpenAI Codex 额度 | 预期脚本：`tools/quota_query.py`；当前本地缺失 | 待接入 | 严禁输出 access token / refresh token |
| `额度切换` | `Codex切换`, `账号切换` | 按 Codex 剩余额度调整账号优先级 | 预期脚本：`tools/codex_quota_preflight.py`；当前本地缺失 | 待接入 | 只输出账号标签/额度状态，不输出密钥 |
| `塔维切换` | `Tavily切换`, `搜索切换`, `塔维账号` | 检查 Tavily 多账号 key 状态并选择可用账号 | 预期脚本：`tools/tavily_key_preflight.py --check-all`；当前本地缺失 | 待接入 | 严禁输出 Tavily API key |
| `当前模式` | - | 显示当前协议模式 | 读取当前 protocol mode 状态；协议状态系统需补齐统一脚本 | 待接入 | 只读 |
| `架构模式` | - | 切换到架构模式 | 通过 protocol mode system 设置 `architect_mode`；统一脚本待补齐 | 待接入 | 不自动改变生产服务 |
| `稳定模式` | - | 切换到稳定模式 | 通过 protocol mode system 设置 `stable`；统一脚本待补齐 | 待接入 | 不自动改变生产服务 |
| `API模型` | - | 使用 API-first 模型策略 | `python3 tools/model_mode_state.py set api --source shortcut` | 已接入 | workspace-local 状态；不改 OpenClaw 全局模型，除非明确要求 |
| `本地模型` | - | 使用 local GPU-first 模型策略 | `python3 tools/model_mode_state.py set local --source shortcut` | 已接入 | 本地 LLM 前检查 VRAM；不超过 9,728 MiB |
| `混合模型` | - | 使用 API + local GPU 混合策略 | `python3 tools/model_mode_state.py set hybrid --source shortcut` | 已接入 | 默认推荐模式 |
| `当前模型` | - | 显示当前模型、上下文、额度、fallback 和路由状态 | `session_status` + `tools/model_runtime_status.py` | 已接入 | 不输出凭证 |
| `模型策略` | - | 显示 API / 本地 / 混合模型策略 | 总结 `docs/model_runtime_strategy.md` | 已接入 | 只读 |
| `上下文预算` | `Context预算` | 显示 1M API context 预算和当前 session 预算 | `python3 tools/api_context_budget.py`；当前 session 用 `--current-session` | 已接入 | 只读 |
| `路由决策` | - | 判断任务应走 API、本地还是混合 | `python3 tools/model_route_decision.py --task-type <type>` | 已接入 | 本地路径需检查 VRAM |
| `服务检查` | `系统检查` | 检查 OpenClaw gateway、Docker 服务、Redis、Qdrant、ComfyUI、模型状态 | 组合 `session_status`, `docker ps`, Redis/Qdrant/ComfyUI health checks | 已接入 | 默认只读；不重启服务 |
| `GitHub状态` | `仓库状态` | 查看 GitHub remote、本地 ahead/behind、最近提交 | `git status`, `git fetch origin --prune`, `gh repo view` | 已接入 | 不 push、不 merge，除非 Jason 明确要求 |
| `系统备份` | - | 执行完整 OpenClaw 系统备份 | 使用 `openclaw-backup` skill 的 `scripts/backup.sh` | 待确认 | 备份含敏感配置；执行前必须 Jason 明确确认 |

## 当前重点缺口

- `daily_news.md` 和 `daily_ai.md` 当前本地缺失，需要重建为 workflow spec。
- `tools/quota_query.py`, `tools/codex_quota_preflight.py`, `tools/tavily_key_preflight.py` 当前本地缺失，不能假装已可执行。
- protocol mode 需要一个统一的本地状态脚本，避免 `当前模式` / `架构模式` / `稳定模式` 只是文档化入口。
- GitHub 远端包含旧备份和分散实现，应按功能 cherry-pick/重写，不做整仓恢复。
