# =========================================
# OpenClaw Daily News Workflow SOP
# File: workflows/daily_news.yaml
# =========================================

name: "Daily_News.md"

description: >
  大马与全球联动新闻执行协议。当用户输入 “今日新闻” 时自动触发。
  使用 Intel + Ops 双阶段执行，避免 context 爆炸与 hallucination。

version: "2.3"

# =========================================
# TRIGGER
# =========================================

trigger:

  exact_match:
    - "今日新闻"
    - "/今日新闻"

# =========================================
# AGENT ROUTING
# =========================================

pipeline:

  - stage: "intel_collection"
    agent: "@intel"

  - stage: "intel_filtering"
    agent: "@intel"

  - stage: "ops_formatting"
    agent: "@ops"

# =========================================
# TOOL ACCESS
# =========================================

allowed_tools:
  - "browser"
  - "ddg-search"
  - "google_search"

# =========================================
# SOURCE PRIORITY
# =========================================

sources:

  local_telegram:

    - name: "星洲日报"
      url: "https://t.me/s/sinchewtelegram"

    - name: "东方日报"
      url: "https://t.me/s/orientaldaily"

    - name: "中国报"
      url: "https://t.me/s/chinapressonline"

    - name: "南洋商报"
      url: "https://t.me/s/nanyangpau"

  international_search:

    - "Reuters AI news last 24 hours"
    - "WSJ global economy"
    - "AI hardware announcements"
    - "semiconductor supply chain"
    - "Middle East oil impact Asia"

# =========================================
# SOURCE SCORING
# =========================================

source_scoring:

  Reuters: 1.00
  "Wall Street Journal": 0.95
  "星洲日报": 0.92
  "东方日报": 0.90
  "中国报": 0.88
  "南洋商报": 0.87

# =========================================
# CACHE LAYER
# =========================================

cache:

  enabled: true

  ttl_minutes: 15

  strategy: "source_level"

# =========================================
# EXECUTION LOGIC
# =========================================

execution:

  local_news:

    fetch_limit_per_source: 5

    output_target: 10

    minimum_required: 5

    extraction_rules:
      - "只提取最近24小时内容"
      - "去除广告"
      - "去除重复新闻"
      - "只保留对普通人有影响的新闻"

  international_news:

    search_limit: 10

    output_target: 5

    extraction_rules:
      - "只保留会影响亚洲或马来西亚的国际新闻"
      - "优先AI、经济、能源、芯片供应链"

# =========================================
# DEDUPLICATION
# =========================================

dedupe_rules:

  similarity_threshold: 0.85

  compare_fields:
    - "title"
    - "summary"

# =========================================
# PRIORITY FILTER
# =========================================

priority_topics:

  high_priority:
    - "马币汇率"
    - "RON95"
    - "生活成本"
    - "教育"
    - "UASA"
    - "AI"
    - "科技"
    - "交通"
    - "芙蓉"
    - "水灾"
    - "大雨"
    - "半导体"
    - "全球供应链"

  medium_priority:
    - "国际贸易"
    - "能源"
    - "电动车"
    - "公共建设"

  remove_topics:
    - "娱乐八卦"
    - "明星绯闻"
    - "政治口水"
    - "党派攻击"
    - "无意义社交媒体争议"

# =========================================
# SAFETY RULES
# =========================================

safety:
  - "禁止编造不存在新闻"
  - "禁止输出未经验证内容"
  - "禁止生成假数据"
  - "新闻不足时必须明确说明"

fallback:

  telegram_unavailable:

    action:
      - "使用 google_search 搜索替代来源"
      - "标记为 fallback source"

  insufficient_news:

    action:
      - "允许输出少于15条"
      - "不得编造补足"

# =========================================
# OUTPUT STYLE
# =========================================

style:

  tone: "茶餐室聊天风"

  requirements:
    - "自然"
    - "简洁"
    - "不要官腔"
    - "适合手机阅读"

  common_phrases:
    - "简单来说就是..."
    - "大家出入要注意..."
    - "这波AI浪潮咱们得跟上..."
    - "世界那边在闹着..."

# =========================================
# OUTPUT TEMPLATE
# =========================================

output:

  title: "📰 今日重点新闻（全球 & 大马联动版）"

  category_headers:
    enabled: true
    numbered: false
    render_once_per_group: true

  numbering:
    enabled: true
    dynamic: true
    start: 1
    max: 15
    style: "telegram_number"
    numbering_mode: "runtime_generated"

  structure: |

    📅 日期：{{current_date}}

    {{category_header}}

    [{{news_index}}] 【{{title}}】

    👉 核心细节：{{summary}}

    👉 影响：{{impact}}

  ending: |

    📊 总结一句

    👉 今日趋势：{{daily_trend}}

# =========================================
# OUTPUT SCHEMA
# =========================================

runtime_output_schema:

  news_item:

    fields:
      - title
      - summary
      - impact
      - category
      - source

# =========================================
# PERFORMANCE OPTIMIZATION
# =========================================

optimization:

  intel_mode:
    - "Intel 只返回结构化摘要"
    - "禁止返回完整网页HTML"
    - "禁止长文本复制"

  ops_mode:
    - "Ops 负责最终排版"
    - "Ops 负责口语化"
    - "Ops 不负责新闻编号生成"

  context_protection:

    max_context_usage_percent: 70

    truncate_rules:
      - "优先删除重复新闻"
      - "优先删除低优先级国际新闻"

# =========================================
# CATEGORY DISPLAY RULES
# =========================================

categories:

  international:
    header: "🌏 国际风云"

  ai_tech:
    header: "🤖 科技与 AI"

  malaysia:
    header: "🇲🇾 大马本地"

  economy:
    header: "💰 经济与民生"

# =========================================
# MEMORY TAGGING
# =========================================

memory:

  qdrant_tags:
    - "daily_news"
    - "news_sop"
    - "malaysia_news"
    - "ai_news"

  retrieval_mode: "semantic"

# =========================================
# RUNTIME ENFORCEMENT
# =========================================

runtime_rules:

  - "Only actual news items receive numbering"
  - "Category headers must never be numbered"
  - "Numbering generated by runtime, not LLM"
  - "Sequential numbering only"
  - "No duplicated numbering"
  - "Category headers rendered once per group"

# =========================================
# END OF FILE
# =========================================