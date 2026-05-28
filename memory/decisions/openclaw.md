# OpenClaw Architecture Decisions

## 2026-05-22: Hybrid Model Runtime Baseline

Decision: Use a hybrid routing policy.

- API model is the default orchestrator for complex, long-context, and tool-heavy work.
- Ollama is the local worker layer for private, compact, and low-risk tasks.
- `qwen3.5:9b` is the primary local reasoning model when VRAM is safe.
- `qwen3.5:4b` and `qwen3.5:2b` are fallbacks for lower-latency or lower-VRAM work.
- `nomic-embed-text:latest` is the local embedding model.
- GitHub is version control for reviewed files, not an automatic backup restore source.

## 2026-05-22: Context-Resilient Runtime Upgrade

Decision: Make context pressure and provider failure first-class routing concerns.

- Live context is capped by policy and should be compressed/offloaded before it becomes a blocker.
- Long outputs and durable decisions must be stored as files, then referenced by path.
- API unavailability triggers a local Ollama fallback path.
- Local fallback is scoped to compact reasoning, local file work, summarization, routing, and embeddings.
- Internet-current or high-complexity claims still require API/search recovery or explicit degraded-mode reporting.

## 2026-05-22: API Context Maximization and GitHub Governance

Decision: API model calls should maximize the effective context budget, while GitHub acts as the setup consultation and version-control trail.

- Official OpenAI model specs define the upper context window.
- OpenClaw runtime/session status defines the practical cap when it is smaller than the official model window.
- Effective context budget is the lower of the model spec window and observed runtime cap.
- Output and reasoning tokens must be reserved inside the context window.
- GitHub-backed setup changes should be committed as small reviewable units and not copied from old backups blindly.

## 2026-05-22: 1M Context Patch Applied

Decision: Configure `openai/gpt-5.5` with Codex agent runtime as the default 1M-context runtime entry for new OpenClaw sessions.

- Persistent OpenClaw config now advertises `openai/gpt-5.5` with a 1,000,000-token context window and Codex auth routing.
- `openclaw models list` shows the configured default as approximately 977K visible context.
- Existing sessions retain their prior 272K cap until gateway restart and fresh session creation.
- Budget tooling must distinguish configured runtime budget from current-session budget.

## 2026-05-24: AI Memory Layer 评估 & 路线

**上下文:** Jason 问 AI Memory Layer 全景，评估 Mem0 集成 ROI

### 评估结论

| 方案 | 决策 | 理由 |
|---|---|---|
| Mem0 | ❌ 不集成 | ROI 低（3/10），自动提取精度 ~60-70%，多依赖 + embedding 费用 |
| MemGPT/Letta | ❌ 不集成 | LLM 自主管理不可预测，架构耦合重 |
| LangGraph Checkpoint | ⏳ 冷藏 | 等照片 Phase 4 启动时再评估 |

### 当前路线

- **现在:** 手动写 MEMORY.md + memory/*.md
- **近期:** `tools/memory_extract.py` 半自动提取 (已实现)
- **中期:** cron 定期跑 memory_extract → review → 写入
- **长期:** 需要时再评估 Mem0/MemGPT（知识保留）

### 已知局限

- Session 日志路径匹配尚未验证（首次跑 sessions 候选为 0）
- `memory_extract.py` 模式匹配精度有限，需要人工 review

## 2026-05-24: Memory Layer 全景评估（补充）

**上下文:** Jason 问 Mem0、Zep、LlamaIndex 评估

### 方案对比

| 方案 | 定位 | 决策 | 理由 |
|---|---|---|---|
| Mem0 | 自动记忆层 | ❌ 不集成 | ROI 低，自动提取精度 ~60-70%，多依赖 |
| Zep | 生产级记忆 BaaS | ❌ 不集成 | 比 Mem0 更重，除非未来需要知识图谱 |
| LlamaIndex | 数据索引框架 | ⏳ 观察 | RAG/文档问答唯一真用途，现在无用 |

### 对现有方案的影响

- 当前 `memory/` + `memory_search` + Qdrant + `tools/memory_extract.py` 覆盖了核心需求
- 未来需要 "D: 盘文件搜索" 时考虑 LlamaIndex
- 未来需要知识图谱实体提取时考虑 Zep
- LangGraph 冷藏，等照片 Phase 4 启动

### 当前路线（重申）

1. ✅ 手动 MEMORY.md + memory/*.md
2. ✅ `tools/memory_extract.py` 半自动提取
3. ⏳ cron 定期跑 memory_extract（待启用）
4. ❌ Mem0/Zep/LlamaIndex 现阶段不集成

## 2026-05-24: AI Eval Layer & 技术选型总结

**上下文:** 调研了 AI Eval 层方案及其他相关技术

### 已实现

| 组件 | 状态 | 说明 |
|---|---|---|
| LangFuse 自托管 | ✅ 生产就绪 | 6 容器, localhost:3000, trace 创建/查询正常 |
| `tools/observability.py` | ✅ | init/trace/query 全功能 |
| `tools/eval_gate.py` | ✅ | faithfulness/hallucination/toxicity/relevancy |
| Eval Judge | ✅ DeepSeek Chat | 走 openclaw infer，零额外成本 |
| Eval → LangFuse 推送 | ✅ | 评测结果写入 Dashboard |

### 技术选型

| 方案 | 决策 | 理由 |
|---|---|---|
| DeepEval | ❌ 不装 | eval_gate.py 已覆盖核心指标，DeepSeek 零成本 judge |
| RAGAS | ❌ 不装 | 没有 RAG pipeline，未来需要再说 |
| OpenRouter | ❌ 不接 | DeepSeek + GPT-5.5 (Codex) 已覆盖，多一层网关多一个故障点 |
| Groq | ❌ 不接 | 加速 eval judge 不是当前瓶颈 |
| vLLM | ⏳ 观察 | Ollama 不稳定时备选；12GB VRAM 限制发挥空间 |
| Helicone | ❌ 不接 | 数据隐私 + SaaS + 已有 LangFuse |

### Eval 层当前精度

DeepSeek Chat 做 judge：
- Faithfulness: ✅ 准确
- Hallucination: ✅ 准确
- Toxicity: ⚠️ 偏低，阈值需从 0.5 下调
- Relevancy: ⚠️ 偏严格，可调 prompt 或换模型

### 下一阶段（待启动）

1. @intel 集成：输出 → faithfulness → < 0.7 重新搜索
2. @sentinel 集成：输出 → toxicity → > 0.2 拦截
3. 照片 Phase 4 启动时重评 LangGraph

## 2026-05-24: Docling (文档解析)

| 方案 | 决策 | 理由 |
|---|---|---|
| Docling | ⏳ 存档 | @intel 需要读 PDF 时再装，~2GB 模型 |
