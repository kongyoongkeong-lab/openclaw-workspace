#!/bin/bash
# Performance regression detector
BASELINE="reports/benchmarks/BASELINE.md"
TODAY="reports/benchmarks/$(date +%Y-%m-%d).md"

[ ! -f "$BASELINE" ] && echo "No baseline yet — run benchmark.sh first" && exit 0
[ ! -f "$TODAY" ] && echo "No today's data — run benchmark.sh first" && exit 0

echo "🔍 Performance Regression Check — $(date)"
REGRESSIONS=0

while IFS='|' read -r _ name time _; do
  name=$(echo "$name" | xargs)
  time=$(echo "$time" | xargs | sed 's/ms//')
  [ -z "$time" ] || [ "$time" = "Time" ] && continue
  base_val=$(grep "| $name |" "$BASELINE" | cut -d'|' -f3 | sed 's/ms//' | xargs)
  [ -z "$base_val" ] && continue
  if [ "$time" -gt $((base_val * 2)) ] 2>/dev/null; then
    echo "  ⚠️ REGRESSION: $name — ${time}ms (baseline: ${base_val}ms)"
    REGRESSIONS=$((REGRESSIONS + 1))
  fi
done < <(tail -n +4 "$TODAY" | head -n -2)

[ "$REGRESSIONS" -eq 0 ] && echo "  ✅ No regressions" || echo "  ❌ $REGRESSIONS regressions"
