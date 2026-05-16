# =========================================
# OpenClaw Weekly AI Insights SOP
# File: workflows/ai_news_weekly.yaml
# Version: 3.5 (Perfected for Local Inference)
# =========================================

name: "AI_Weekly_Pulse.md"

description: >
  针对 Pentagon Stack 优化的 AI 周报协议。
  严格聚焦 7 天内动态，包含模型量化、本地部署可行性及大马 AI 政策。

# =========================================
# TRIGGER (触发暗号)
# =========================================

trigger:
  exact_match:
    - "AI新闻"
    - "/AI周报"
    - "一周AI"
    - "AI日报"

# =========================================
# AGENT ROUTING (Intel 收集 + Ops 翻译)
# =========================================

pipeline:
  - stage: "intel_discovery"   # 任务：深度扫描、去重、提取 Benchmark
    agent: "@intel"
  - stage: "ops_synthesis"    # 任务：将参数转化为“4070S 能不能跑”的人话
    agent: "@ops"

# =========================================
# AI-SPECIFIC SOURCES (权威信源)
# =========================================

sources:
  direct_feed:
    - name: "The Rundown AI / Ben's Bites"
    - name: "Hugging Face Daily Papers"
    - name: "LocalLLaMA (Reddit)" # 对 4070S 极具参考价值的本地部署社区
  
  official_channels:
    - "OpenAI / Anthropic / Google DeepMind"
    - "NVIDIA Newsroom (针对驱动与 CUDA 更新)"
    - "Meta AI / Mistral / DeepSeek (开源主力)"

  local_relevance:
    - "Digital Ministry Malaysia (Kementerian Digital)"
    - "MDEC / MyDIGITAL Updates"

# =========================================
# SEARCH STRATEGY (4070S 专属优化)
# =========================================

search_parameters:
  time_range: "past_7_days"
  priority_queries:
    - "Latest LLM GGUF / EXL2 quantization updates this week"
    - "Ollama / Docker AI stack new features past 7 days"
    - "NVIDIA RTX 40 series driver / performance optimizations"
    - "Malaysia AI Sandbox / National AI Office updates"
    - "New open-source models under 30B parameters (4070S friendly)"

# =========================================
# EXECUTION & FILTERING (核心规则)
# =========================================

execution:
  ai_focus:
    output_target: 15
    extraction_rules:
      - "Strictly past 7 days (必须包含具体发布日期)"
      - "优先保留：模型性能突破、本地显存优化、大马落地政策"
      - "剔除：无关痛痒的厂商公关稿、无代码发布的 Demo、非 AI 类的普通科技新闻"
      - "量化关注：必须提及新模型是否适合 12GB VRAM 运行"

# =========================================
# OUTPUT STYLE (茶餐室聊 AI)
# =========================================

style:
  tone: "茶餐室聊天风"
  common_phrases:
    - "简单来说，这对咱们 Pentagon Stack 意味着..."
    - "好消息，咱们那块 4070 SUPER 又有新玩具玩了..."
    - "这波 AI 浪潮咱们得跟上，其实就是..."
    - "别被这些术语吓到，简单来说就是..."

# =========================================
# OUTPUT STRUCTURE (带全局编号)
# =========================================

output:
  title: "🤖 全球 AI 周报（过去 7 天精华版）"
  
  # 强制执行全局连续编号，不随分类重置
  global_sequential_numbering: true

  structure: |
    📅 日期：{{current_date}}
    📈 周期：过去 7 天精华汇总

    {{category_header}}
    {{news_index}}️⃣ **【{{title}}】**
    👉 核心细节：{{summary_brief}}
    💡 影响：{{hardware_relevance_or_impact}}

  ending: |
    📊 总结一句
    👉 本周风向：{{daily_trend}}

# =========================================
# RUNTIME RULES (运行守则)
# =========================================

runtime_rules:
  - "Global numbering: Start from 1 up to 15 across ALL categories"
  - "Category headers must be rendered as separators, never numbered"
  - "If less than 15 items found, provide the actual count, do NOT hallucinate"
  - "Impact field must explicitly mention if it's '4070S compatible' or 'Cloud only'"

# =========================================
# OPTIMIZATION (显存与上下文保护)
# =========================================

optimization:
  intel_mode:
    - "只提取模型名、参数量(B)、上下文长度(K)和核心 Benchmark"
  ops_mode:
    - "负责将量化术语（如 Q4_K_M）转化为『显存占用情况』"
    - "确保语气亲切，适合在手机 Telegram 阅读"

# =========================================
# END OF SOP
# =========================================