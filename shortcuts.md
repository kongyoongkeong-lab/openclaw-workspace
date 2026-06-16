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
| `指令体检` | `快捷体检`, `Shortcut体检`, `shortcut audit` | 只读检查快捷指令注册表中的本地路径、状态字段、高风险安全提示和静态能力矩阵 | `python3 tools/shortcut_doctor.py audit --deep`，报告写入 `D:\_outbox\reports\shortcut_doctor\` | 已接入 | 只读；不执行快捷指令目标命令；不读取或输出密钥 |
| `快捷状态` | `shortcut_status`, `/shortcut_status` | 显示轻量 shortcut governance 状态：总数、分组、风险、确认类、隔离状态和最近 usage log；可按 group 查看 `photo/model/backup/automation/system/news/github` | `python3 tools/shortcut_status.py status [group]`；结构化 manifest 由 `python3 tools/shortcut_doctor.py manifest --write config/shortcut_manifest.json` 生成；usage log 写入 `data/shortcut_usage/shortcut_usage.jsonl` | 已接入 | 只读状态；不执行快捷指令目标命令；不读取或输出密钥；报告只引用本地 manifest 和 usage log |
| `今日新闻` | `每日新闻`, `daily news` | 生成每日新闻，优先使用 6 小时内缓存 | 执行 `daily_news.md` workflow spec，归档到 `news/YYYY-MM-DD_daily_news.md` | 已接入 | 搜索来源需可追溯；不刷新除非 Jason 明确要求；输出证据保存在 `news/` |
| `刷新新闻` | `重新抓取`, `重新生成今日新闻`, `deep search`, `深度搜索` | 强制刷新每日新闻缓存 | `daily_news.md` / `daily_ai.md` workflow 的刷新模式 | 已接入 | 明确刷新才联网重抓 |
| `今日AI` | `今日 AI`, `AI日报`, `最新AI动态` | 生成最近 7 天 AI 日报 | 执行 `daily_ai.md` workflow spec，归档到 `news/ai/YYYY-MM-DD_daily_ai.md` | 已接入 | 需标注日期和来源；输出证据保存在 `news/ai/` |
| `额度查询` | - | 查询 ChatGPT Plus / OpenAI Codex 额度；覆盖 `openai-codex:kongyoongkeong@gmail.com` 和 `openai-codex:wahlquistmetallohk619@gmail.com` | `python3 tools/quota_query.py`；dry-run 用 `python3 tools/quota_query.py --profiles-only`；self-test 用 `python3 tools/quota_query.py --self-test` | 已接入 | 只输出账号标签/额度状态；严禁输出 access token / refresh token / API key；输出证据为 Telegram 回执或 `data/shortcut_usage/shortcut_usage.jsonl` |
| `额度切换` | `Codex切换`, `账号切换` | 按 Codex 剩余额度调整账号优先级 | `python3 tools/codex_quota_preflight.py`；dry-run 用 `python3 tools/codex_quota_preflight.py --dry-run`；self-test 用 `python3 tools/codex_quota_preflight.py --self-test` | 已接入 | 只输出账号标签/额度状态，不输出密钥；状态证据为 `data/shortcut_usage/shortcut_usage.jsonl` |
| `塔维切换` | `Tavily切换`, `搜索切换`, `塔维账号` | 检查 Tavily 多账号 key 状态并选择可用账号 | `python3 tools/tavily_key_preflight.py --check-all`；dry-run 用 `python3 tools/tavily_key_preflight.py --list-only --no-write`；self-test 用 `python3 tools/tavily_key_preflight.py --self-test` | 已接入 | 严禁输出 Tavily API key；状态证据为 `config/tavily_key_state.json` |
| `HF状态` | `Hugging Face`, `模型仓库` | 检查 Hugging Face CLI、token、公开模型访问状态 | `python3 tools/huggingface_preflight.py --list-only`；需要账号验证时使用 `--whoami`；self-test 用 `python3 tools/huggingface_preflight.py --self-test` | 已接入 | 严禁输出 Hugging Face token；状态证据为 `config/huggingface_state.json` |
| `模型下载` | `HF下载`, `下载模型` | 规划并安全下载 Hugging Face 模型到 `/mnt/d/models/huggingface/` | 先运行 `python3 tools/huggingface_download.py <org/model-id>`；dry-run 默认只打印 plan；self-test 用 `python3 tools/huggingface_download.py --self-test`；实际下载需加 `--yes` | 已接入 | 严禁输出 Hugging Face token；默认不下载，需显式 `--yes`；下载证据为 `/mnt/d/models/huggingface/` 内 manifest |
| `当前模式` | - | 显示当前协议模式 | `python3 tools/protocol_mode_state.py get`；self-test 用 `python3 tools/protocol_mode_state.py self-test` | 已接入 | 只读 |
| `架构模式` | - | 切换到架构模式 | `python3 tools/protocol_mode_state.py set architect_mode --source shortcut`；dry-run 用 `python3 tools/protocol_mode_state.py set architect_mode --source shortcut --dry-run`；self-test 用 `python3 tools/protocol_mode_state.py self-test` | 已接入 | 不自动改变生产服务；状态证据为 `config/protocol_mode.json` |
| `稳定模式` | - | 切换到稳定模式 | `python3 tools/protocol_mode_state.py set stable --source shortcut`；dry-run 用 `python3 tools/protocol_mode_state.py set stable --source shortcut --dry-run`；self-test 用 `python3 tools/protocol_mode_state.py self-test` | 已接入 | 不自动改变生产服务；状态证据为 `config/protocol_mode.json` |
| `API模型` | - | 使用 API-first 模型策略 | `python3 tools/model_mode_state.py set api --source shortcut`；dry-run 用 `python3 tools/model_mode_state.py set api --source shortcut --dry-run`；self-test 用 `python3 tools/model_mode_state.py self-test` | 已接入 | workspace-local 状态；不改 OpenClaw 全局模型，除非明确要求；状态证据为 `config/model_runtime.json` |
| `本地模型` | - | 使用 local GPU-first 模型策略 | `python3 tools/model_mode_state.py set local --source shortcut`；dry-run 用 `python3 tools/model_mode_state.py set local --source shortcut --dry-run`；self-test 用 `python3 tools/model_mode_state.py self-test` | 已接入 | 本地 LLM 前检查 VRAM；不超过 9,728 MiB；状态证据为 `config/model_runtime.json` |
| `混合模型` | - | 使用 API + local GPU 混合策略 | `python3 tools/model_mode_state.py set hybrid --source shortcut`；dry-run 用 `python3 tools/model_mode_state.py set hybrid --source shortcut --dry-run`；self-test 用 `python3 tools/model_mode_state.py self-test` | 已接入 | 默认推荐模式；状态证据为 `config/model_runtime.json` |
| `当前模型` | - | 显示当前模型、上下文、额度、fallback 和路由状态 | `session_status` + `python3 tools/model_runtime_status.py`；dry-run 用 `python3 tools/model_runtime_status.py --dry-run`；self-test 用 `python3 tools/model_runtime_status.py --self-test` | 已接入 | 不输出凭证；输出证据为 Telegram 回执或 `data/shortcut_usage/shortcut_usage.jsonl` |
| `模型策略` | - | 显示 API / 本地 / 混合模型策略 | 总结 `docs/model_runtime_strategy.md` | 已接入 | 只读 |
| `上下文预算` | `Context预算` | 显示 1M API context 预算和当前 session 预算 | `python3 tools/api_context_budget.py`；当前 session 用 `--current-session`；self-test 用 `python3 tools/api_context_budget.py --self-test` | 已接入 | 只读 |
| `路由决策` | - | 判断任务应走 API、本地还是混合 | `python3 tools/model_route_decision.py --task-type <type>`；self-test 用 `python3 tools/model_route_decision.py --self-test` | 已接入 | 本地路径需检查 VRAM |
| `服务检查` | `系统检查` | 检查 OpenClaw gateway、Docker 服务、Redis、Qdrant、ComfyUI、Langfuse、模型/GPU、磁盘状态 | `python3 tools/system_health_check.py`；详细输出用 `--details`；机器输出用 `--json`；self-test 用 `python3 tools/system_health_check.py --self-test` | 已接入 | 默认只读；不重启服务；输出需脱敏 |
| `GitHub状态` | `仓库状态` | 查看 GitHub remote、本地 ahead/behind、最近提交 | `git status`, `git fetch origin --prune`, `gh repo view` | 已接入 | 不 push、不 merge，除非 Jason 明确要求；输出证据为 Telegram 回执或 `data/shortcut_usage/shortcut_usage.jsonl` |
| `重启网关` | - | 重启 OpenClaw Gateway 服务 | 先运行 `python3 tools/pending_action.py ask --id gateway-restart --title "Restart OpenClaw Gateway" --summary "Restart OpenClaw gateway; active sessions may disconnect briefly." --risk medium --source telegram-prompt`；dry-run 用 `python3 tools/pending_action.py get`；确认后才执行 `openclaw gateway restart` | 已接入 | 需确认；重启期间短暂离线，已连接会话会断开；确认前必须登记 pending_action；状态证据为 `config/pending_action.json` |
| `自动协议` | `automation-protocol` | 使用已验证的 Chrome CDP / Playwright / Windows 文件路由自动化协议 | `skills/automation-protocol/SKILL.md`；dry-run 文件探测 `python3 skills/automation-protocol/scripts/automation_file_probe.py find <name>`；self-test 用 `python3 skills/automation-protocol/scripts/automation_file_probe.py self-test` | 已接入 | CDP 视为敏感浏览器控制；不做支付/账号更改/破坏性文件操作，除非明确确认；输出证据为 `shared/artifacts/` 或 `D:\_outbox\` |
| `PDF转PPT` | `PDF转PPTX`, `pdf2pptx` | 将 PDF 转换为 PowerPoint 并验证输出 | 优先按 `automation-protocol` 使用 iLovePDF CDP 流程；已验证脚本 `/mnt/c/Users/jason/OpenClaw/tools/pdf2pptx_convert.mjs`；dry-run 先用 `python3 skills/automation-protocol/scripts/automation_file_probe.py find <pdf>`；self-test 用 `python3 skills/automation-protocol/scripts/automation_file_probe.py self-test`；输出验证用 `python3 skills/automation-protocol/scripts/automation_file_probe.py verify <pptx>` | 已接入 | 上传前确认目标文件；输出必须验证路径、大小、时间戳 |
| `检查浏览器` | `Chrome检查`, `浏览器检查` | 检查 Chrome CDP 可见页面、URL、标题和关键网页状态 | `automation-protocol` + Playwright CDP tab probe | 已接入 | 只读检查；不读取敏感网页内容，除非任务需要 |
| `视频重试` | `重试视频`, `豆包重试`, `Gemini重试` | 重试已验证的 Gemini/豆包图片生成视频流程 | `automation-protocol` 中的 Gemini/Doubao 模板；沿用上次 prompt、图片路径、服务错误记录 | 已接入 | 服务过载时停止循环；不重复无意义提交；输出证据保存在 `shared/artifacts/` 或 `D:\_outbox\` |
| `技能更新` | `更新技能`, `创建技能` | 创建或更新 OpenClaw skill，并验证 frontmatter | 使用 `skill-creator` skill；验证命令 `python3 .../skill-creator/scripts/quick_validate.py <skill-dir>` | 已接入 | 不安装外部 skill；外部来源需先 vet |
| `系统备份` | - | 执行完整 OpenClaw 系统备份 | 使用 `scripts/backup.sh --dry-run` 进行接入检查；真实备份待 `openclaw-backup` skill 接入后执行 | 待确认 | 备份含敏感配置；执行前必须 Jason 明确确认；self-test 用 `scripts/backup.sh --self-test`；目标证据为 `D:\backup\` |

## 当前重点缺口

- `系统备份` 保持待确认，因为备份含敏感配置，执行前必须 Jason 明确确认。
- Hugging Face 已接入本地 preflight 和安全下载 planner，账号 `jason2ykk` 已验证；gated/private model 下载仍需逐个模型先在 Hugging Face 接受 license/access。
- GitHub 远端包含旧备份和分散实现；本地规则已固定为按功能 cherry-pick/重写，不做整仓恢复。
