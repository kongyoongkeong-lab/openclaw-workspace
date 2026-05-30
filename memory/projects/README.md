# Project Memory

Use one subdirectory per durable project. Each project directory should prefer
these files when useful:

| File | Purpose |
|---|---|
| `overview.md` | Stable project purpose, boundaries, and current status. |
| `decisions.md` | Project-specific decisions not broad enough for `memory/decisions/`. |
| `runbooks.md` | Repeatable local procedures and verification steps. |
| `open-questions.md` | Unresolved questions and blocked follow-ups. |

Avoid raw logs here. Link to `memory/logs/` entries when chronological context
is needed.
