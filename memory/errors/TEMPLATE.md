# Failure Entry Template

```markdown
## ERR-YYYYMMDD-NNN — short title

**Date:** YYYY-MM-DD
**Priority:** low | medium | high | critical
**Status:** open | mitigated | fixed | watch
**Area:** model | docker | n8n | browser | windows | pdf | image | video | memory | search | security | docs | other
**Detected By:** user | @main | @intel | @ops | @sentinel | tool | test

### Summary
One concise sentence describing the failure.

### Trigger
- Command/workflow:
- Input class:
- Environment:

### Error Signal
Short sanitized error message or symptom.

### Root Cause
What actually caused the failure.

### Recovery
What worked this time.

### Prevention Rule
What future agents should do first to avoid repeating this.

### Related
- Files:
- Services:
- See also:
```

