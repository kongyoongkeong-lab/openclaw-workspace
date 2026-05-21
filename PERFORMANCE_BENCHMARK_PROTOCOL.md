# ⏱️ Performance Benchmarking Protocol — v1

**Owner:** @sentinel (Guardian)
**Scope:** Agent response times, throughput baselines, regression detection
**Updated:** 2026-05-22

## Benchmark Baselines

| Agent | Operation | Avg Time | P95 | P99 | Target |
|-------|-----------|----------|-----|-----|--------|
| @intel | Search (cache hit) | 0.5s | 1s | 2s | ✅ |
| @intel | Search (cache miss - GitHub) | 3s | 5s | 8s | ✅ |
| @intel | Search (cache miss - Web) | 8s | 15s | 30s | ⚠️ |
| @ops | Shell command | 2s | 5s | 10s | ✅ |
| @ops | Docker restart | 5s | 8s | 15s | ✅ |
| @ops | GitHub push | 8s | 12s | 20s | ✅ |
| @comms | Message delivery | 1s | 2s | 5s | ✅ |
| @sentinel | Secret scan | 1s | 2s | 3s | ✅ |
| **System** | Full task (search→exec→report) | 15s | 30s | 60s | ⚠️ |

## Benchmark Runner

```bash
#!/bin/bash
# benchmark.sh — run performance benchmarks and report

REPORT_DIR="$HOME/.openclaw/workspace/reports/benchmarks"
mkdir -p "$REPORT_DIR"
DATE=$(date +%Y-%m-%d)
FILE="$REPORT_DIR/$DATE.md"

echo "# Benchmark Report — $DATE" > "$FILE"
echo "| Test | Time | Result |" >> "$FILE"
echo "|------|------|--------|" >> "$FILE"

run_test() {
  local name=$1 cmd=$2
  local start=$(date +%s%N)
  eval "$cmd" >/dev/null 2>&1
  local end=$(date +%s%N)
  local elapsed_ms=$(( (end - start) / 1000000 ))
  local status=$([ $? -eq 0 ] && echo "✅" || echo "❌")
  echo "| $name | ${elapsed_ms}ms | $status |" >> "$FILE"
}

# Agent tests
run_test "GitHub API" "gh api repos/kongyoongkeong-lab/openclaw-workspace"
run_test "Qdrant ping" "curl -s http://localhost:6333/healthz"
run_test "Redis ping" "echo PING | redis-cli"
run_test "ComfyUI ping" "curl -s http://localhost:8188/"
run_test "Shell echo" "echo hello"
run_test "Git status" "cd ~/.openclaw/workspace && git status"

echo "" >> "$FILE"
echo "---" >> "$FILE"
echo "Run: $(date)" >> "$FILE"
```

## Performance Regression Detection

```bash
#!/bin/bash
# detect_regression.sh — compare today's benchmarks to baseline

BASELINE="$HOME/.openclaw/workspace/reports/benchmarks/BASELINE.md"
TODAY="$HOME/.openclaw/workspace/reports/benchmarks/$(date +%Y-%m-%d).md"

if [ ! -f "$BASELINE" ]; then
  echo "No baseline found. Creating from today's run."
  cp "$TODAY" "$BASELINE"
  git add "$BASELINE"
  git commit -m "benchmark: establish baseline — $(date +%Y-%m-%d)"
  git push origin master
  exit 0
fi

# Compare — flag anything > 2x baseline
echo "🔍 Performance Regression Check — $(date)"
REGRESSIONS=0

while IFS='|' read -r _ name time _; do
  base_val=$(grep "| $name |" "$BASELINE" | cut -d'|' -f3 | tr -d ' ms')
  [ -z "$base_val" ] && continue

  if [ "$time" -gt $((base_val * 2)) ] 2>/dev/null; then
    echo "  ⚠️ REGRESSION: $name — ${time}ms (baseline: ${base_val}ms)"
    REGRESSIONS=$((REGRESSIONS + 1))
  fi
done < <(tail -n +4 "$TODAY" | head -n -2)

if [ "$REGRESSIONS" -eq 0 ]; then
  echo "  ✅ No regressions detected"
else
  echo "  ❌ $REGRESSIONS regressions found"
  gh issue create \
    --repo kongyoongkeong-lab/openclaw-workspace \
    --title "[perf] $REGRESSIONS regressions detected — $(date +%Y-%m-%d)" \
    --label "performance" \
    --body "## Regression Report\nDate: $(date)\nRegressions: $REGRESSIONS\n\nSee: reports/benchmarks/$(date +%Y-%m-%d).md"
fi
```

## GitHub Actions: Scheduled Benchmark

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday 6 AM
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run benchmarks
        run: |
          chmod +x benchmark.sh
          ./benchmark.sh
      - name: Check regressions
        run: bash detect_regression.sh
```

## Benchmark Log Format

```markdown
### Benchmark — Agent Response Times (YY-MM-DD)

**Environment:** Cloud-native, WSL2, CPU mode
**Model:** DeepSeek

| Agent | Operation | Avg | P95 | Samples |
|-------|-----------|-----|-----|---------|
| @intel | Search | 2.1s | 4.5s | 10 |
| @ops | Exec | 1.8s | 3.2s | 10 |
| @comms | Format | 0.3s | 0.5s | 10 |

**Regressions vs baseline:** 0 ✅
```

## Files

| File | Purpose |
|------|---------|
| `PERFORMANCE_BENCHMARK_PROTOCOL.md` | This document |
| `benchmark.sh` | Benchmark runner |
| `detect_regression.sh` | Regression comparison |
| `reports/benchmarks/` | Benchmark results (git-tracked) |
| `.github/workflows/benchmark.yml` | Weekly scheduled benchmark |
