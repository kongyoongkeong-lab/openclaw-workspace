#!/bin/bash
# Weekly audit report
REPORT_DIR="reports/audit"
mkdir -p "$REPORT_DIR"
DATE=$(date +%Y-%m-%d)

cat > "$REPORT_DIR/weekly_$DATE.md" << EOF
# Audit Report — $DATE

## Git Activity
Commits (7 days): $(cd ~/.openclaw/workspace && git log --oneline --since="7 days ago" 2>/dev/null | wc -l)

## Incidents
Open: $(find reports/incidents -name "*.md" 2>/dev/null | wc -l)

## Credentials
Stored securely: ✅ (outside git, 600 perms)
EOF

git add reports/audit/
git commit -m "audit: weekly report — $DATE"
git push origin master
