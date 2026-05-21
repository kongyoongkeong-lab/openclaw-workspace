#!/bin/bash
# Performance benchmark runner
REPORT_DIR="reports/benchmarks"
mkdir -p "$REPORT_DIR"
FILE="$REPORT_DIR/$(date +%Y-%m-%d).md"

echo "# Benchmark — $(date)" > "$FILE"
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

run_test "GitHub API" "gh api repos/kongyoongkeong-lab/openclaw-workspace 2>/dev/null"
run_test "Qdrant" "curl -s http://localhost:6333/healthz 2>/dev/null"
run_test "Redis" "echo PING | redis-cli 2>/dev/null"
run_test "ComfyUI" "curl -s http://localhost:8188/ 2>/dev/null"
run_test "Shell echo" "echo hello"
run_test "Git status" "cd ~/.openclaw/workspace && git status 2>/dev/null"

echo "" >> "$FILE"
echo "---" >> "$FILE"
echo "Run: $(date)" >> "$FILE"

# Set baseline on first run
BASELINE="reports/benchmarks/BASELINE.md"
[ ! -f "$BASELINE" ] && cp "$FILE" "$BASELINE" && echo "✅ Baseline established"

echo "✅ Benchmarks written to $FILE"
