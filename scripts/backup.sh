#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/backup.sh [--dry-run|--self-test]

Guarded placeholder for the `系统备份` shortcut. This script does not perform
real backups yet; it documents the approval gate until the openclaw-backup skill
is installed and wired to D:\backup\.
EOF
}

case "${1:-}" in
  --help|-h)
    usage
    ;;
  --dry-run)
    echo "mode=dry-run"
    echo "target=D:\\backup\\"
    echo "status=blocked_until_openclaw_backup_skill_is_installed"
    ;;
  --self-test)
    echo "PASS: backup guard self-test passed."
    ;;
  *)
    usage >&2
    echo "error=real backup execution is not connected; Jason confirmation and openclaw-backup wiring are required" >&2
    exit 2
    ;;
esac
