# Pentagon Workspace

> OpenClaw 多智能体编排系统 — 智能体配置、记忆与基础设施。

## 架构

```
@main (编排器)
 ├── @intel   — 研究：Tavily 搜索、Qdrant 向量检索
 ├── @ops     — 执行：Python、Bash、Docker
 ├── @comms   — 通信：Telegram、Slack
 └── @sentinel— 守护：安全审查、幻觉检测
```

**引擎：** 纯云原生（通过 DeepSeek 等使用云端推理）  
**记忆：** Qdrant 向量数据库 + 文件系统  
**基础设施：** WSL2、Docker、GitHub

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/kongyoongkeong-lab/openclaw-workspace.git
cd openclaw-workspace

# 通过 OpenClaw Gateway 运行
# 详情参见 AGENTS.md、SOUL.md 和 IDENTITY.md
```

## 目录结构

```
├── AGENTS.md          # 智能体角色与层级结构
├── SOUL.md            # 核心身份与操作逻辑
├── IDENTITY.md        # 技术规格与权限
├── USER.md            # 用户画像与偏好
├── HEARTBEAT.md       # 系统健康与稳定性验证
├── intel/             # @intel 智能体配置
├── ops/               # @ops 智能体配置
├── sentinel/          # @sentinel 智能体配置
├── comms/             # @comms 智能体配置
└── memory/            # 长期与短期记忆存储
```

## 环境变量

| 变量 | 用途 |
|------|---------|
| `COMFY_API_KEY` | ComfyOrg API 密钥 |

## 许可证

内部使用 — @kongyoongkeong-lab
