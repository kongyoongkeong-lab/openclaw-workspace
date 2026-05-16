# Baseline Conditioning Schema

## 🚨 核心问题

当前 baseline 定义：
```
baseline = P(metric | time_window)  # 混合分布
```

正确定义应为：
```
baseline = P(metric | workload_type, tool_count, context_depth)  # 条件化分布
```

## 🧩 Conditioning Keys (3 维度)

```json
{
  "tool_count_bucket": "low | medium | high",
  "handoff_depth_bucket": "1-2 | 3-4 | 5+",
  "context_bucket": "0-30% | 30-70% | 70-100%"
}
```

### Bucket Boundaries

**tool_count_bucket:**
- low: 0-1 tools
- medium: 2-4 tools  
- high: 5+ tools

**handoff_depth_bucket:**
- 1-2: 1-2 agent handoffs
- 3-4: 3-4 agent handoffs
- 5+: 5+ agent handoffs

**context_bucket:**
- 0-30%: idle < 30%
- 30-70%: idle 30-70%
- 70-100%: idle > 70%

## 📊 Distribution Storage

每个条件化 baseline 存储为：

```json
{
  "baseline_id": "baseline_<tool_bucket>_<handoff_bucket>_<context_bucket>",
  "conditioning_key": {
    "tool_count_bucket": "medium",
    "handoff_depth_bucket": "3-4",
    "context_bucket": "30-70%"
  },
  "distribution": {
    "metric": "entity_loss_rate",
    "samples": [
      {"timestamp": "...", "value": 0.12},
      ...
    ],
    "mean": 0.11,
    "std": 0.03
  },
  "sample_count": 150,
  "created_at": "..."
}
```

## 🔍 Identification Strategy

每个 baseline 必须包含：

1. **Conditioning Key Hash** - 可验证的条件标识
2. **Sample Diversity Metric** - 样本代表性
3. **Bootstrap Confidence** - 置信区间

## ⚠️ 避免的陷阱

- ❌ 不要使用 time_window 作为 conditioning key
- ❌ 不要依赖 "no stress" 标签
- ❌ 不要混合不同 regime 的样本

## 🚀 下一步

1. 实现 workload_composition_tracker.py
2. 重写 baseline 计算器
3. 迁移历史数据到 conditioning buckets
4. 重新计算 correlation matrix
