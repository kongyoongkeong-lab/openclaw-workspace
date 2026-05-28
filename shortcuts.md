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
| `今日新闻` | `每日新闻`, `daily news` | 生成每日新闻，优先使用 6 小时内缓存 | 执行 `daily_news.md` workflow spec，归档到 `news/YYYY-MM-DD_daily_news.md` | 已接入 | 搜索来源需可追溯；不刷新除非 Jason 明确要求 |
| `刷新新闻` | `重新抓取`, `重新生成今日新闻`, `deep search`, `深度搜索` | 强制刷新每日新闻缓存 | `daily_news.md` / `daily_ai.md` workflow 的刷新模式 | 已接入 | 明确刷新才联网重抓 |
| `今日AI` | `今日 AI`, `AI日报`, `最新AI动态` | 生成最近 7 天 AI 日报 | 执行 `daily_ai.md` workflow spec，归档到 `news/ai/YYYY-MM-DD_daily_ai.md` | 已接入 | 需标注日期和来源 |
| `额度查询` | - | 查询 ChatGPT Plus / OpenAI Codex 额度；覆盖 `openai-codex:kongyoongkeong@gmail.com` 和 `openai-codex:wahlquistmetallohk619@gmail.com` | `python3 tools/quota_query.py` | 已接入 | 只输出账号标签/额度状态；严禁输出 access token / refresh token / API key |
| `额度切换` | `Codex切换`, `账号切换` | 按 Codex 剩余额度调整账号优先级 | `python3 tools/codex_quota_preflight.py` | 已接入 | 只输出账号标签/额度状态，不输出密钥 |
| `塔维切换` | `Tavily切换`, `搜索切换`, `塔维账号` | 检查 Tavily 多账号 key 状态并选择可用账号 | `python3 tools/tavily_key_preflight.py --check-all` | 已接入 | 严禁输出 Tavily API key |
| `HF状态` | `Hugging Face`, `模型仓库` | 检查 Hugging Face CLI、token、公开模型访问状态 | `python3 tools/huggingface_preflight.py --list-only`；需要账号验证时使用 `--whoami` | 已接入 | 严禁输出 Hugging Face token |
| `模型下载` | `HF下载`, `下载模型` | 规划并安全下载 Hugging Face 模型到 `/mnt/d/models/huggingface/` | 先运行 `python3 tools/huggingface_download.py <org/model-id>`；实际下载需加 `--yes` | 已接入 | 严禁输出 Hugging Face token；默认不下载，需显式 `--yes` |
| `当前模式` | - | 显示当前协议模式 | `python3 tools/protocol_mode_state.py get` | 已接入 | 只读 |
| `架构模式` | - | 切换到架构模式 | `python3 tools/protocol_mode_state.py set architect_mode --source shortcut` | 已接入 | 不自动改变生产服务 |
| `稳定模式` | - | 切换到稳定模式 | `python3 tools/protocol_mode_state.py set stable --source shortcut` | 已接入 | 不自动改变生产服务 |
| `API模型` | - | 使用 API-first 模型策略 | `python3 tools/model_mode_state.py set api --source shortcut` | 已接入 | workspace-local 状态；不改 OpenClaw 全局模型，除非明确要求 |
| `本地模型` | - | 使用 local GPU-first 模型策略 | `python3 tools/model_mode_state.py set local --source shortcut` | 已接入 | 本地 LLM 前检查 VRAM；不超过 9,728 MiB |
| `混合模型` | - | 使用 API + local GPU 混合策略 | `python3 tools/model_mode_state.py set hybrid --source shortcut` | 已接入 | 默认推荐模式 |
| `当前模型` | - | 显示当前模型、上下文、额度、fallback 和路由状态 | `session_status` + `tools/model_runtime_status.py` | 已接入 | 不输出凭证 |
| `模型策略` | - | 显示 API / 本地 / 混合模型策略 | 总结 `docs/model_runtime_strategy.md` | 已接入 | 只读 |
| `上下文预算` | `Context预算` | 显示 1M API context 预算和当前 session 预算 | `python3 tools/api_context_budget.py`；当前 session 用 `--current-session` | 已接入 | 只读 |
| `路由决策` | - | 判断任务应走 API、本地还是混合 | `python3 tools/model_route_decision.py --task-type <type>` | 已接入 | 本地路径需检查 VRAM |
| `服务检查` | `系统检查` | 检查 OpenClaw gateway、Docker 服务、Redis、Qdrant、ComfyUI、Langfuse、模型/GPU、磁盘状态 | `python3 tools/system_health_check.py`；详细输出用 `--details`；机器输出用 `--json` | 已接入 | 默认只读；不重启服务；输出需脱敏 |
| `GitHub状态` | `仓库状态` | 查看 GitHub remote、本地 ahead/behind、最近提交 | `git status`, `git fetch origin --prune`, `gh repo view` | 已接入 | 不 push、不 merge，除非 Jason 明确要求 |
| `自动协议` | `automation-protocol` | 使用已验证的 Chrome CDP / Playwright / Windows 文件路由自动化协议 | `skills/automation-protocol/SKILL.md`；文件探测 `python3 skills/automation-protocol/scripts/automation_file_probe.py` | 已接入 | CDP 视为敏感浏览器控制；不做支付/账号更改/破坏性文件操作，除非明确确认 |
| `PDF转PPT` | `PDF转PPTX`, `pdf2pptx` | 将 PDF 转换为 PowerPoint 并验证输出 | 优先按 `automation-protocol` 使用 iLovePDF CDP 流程；已验证脚本 `/mnt/c/Users/jason/OpenClaw/tools/pdf2pptx_convert.mjs`；输出验证用 `automation_file_probe.py verify` | 已接入 | 上传前确认目标文件；输出必须验证路径、大小、时间戳 |
| `检查浏览器` | `Chrome检查`, `浏览器检查` | 检查 Chrome CDP 可见页面、URL、标题和关键网页状态 | `automation-protocol` + Playwright CDP tab probe | 已接入 | 只读检查；不读取敏感网页内容，除非任务需要 |
| `视频重试` | `重试视频`, `豆包重试`, `Gemini重试` | 重试已验证的 Gemini/豆包图片生成视频流程 | `automation-protocol` 中的 Gemini/Doubao 模板；沿用上次 prompt、图片路径、服务错误记录 | 已接入 | 服务过载时停止循环；不重复无意义提交 |
| `技能更新` | `更新技能`, `创建技能` | 创建或更新 OpenClaw skill，并验证 frontmatter | 使用 `skill-creator` skill；验证命令 `python3 .../skill-creator/scripts/quick_validate.py <skill-dir>` | 已接入 | 不安装外部 skill；外部来源需先 vet |
| `系统备份` | - | 执行完整 OpenClaw 系统备份 | 使用 `openclaw-backup` skill 的 `scripts/backup.sh` | 待确认 | 备份含敏感配置；执行前必须 Jason 明确确认 |

## 当前重点缺口

- `系统备份` 保持待确认，因为备份含敏感配置，执行前必须 Jason 明确确认。
- Hugging Face 已接入本地 preflight 和安全下载 planner，账号 `jason2ykk` 已验证；gated/private model 下载仍需逐个模型先在 Hugging Face 接受 license/access。
- GitHub 远端包含旧备份和分散实现；本地规则已固定为按功能 cherry-pick/重写，不做整仓恢复。
