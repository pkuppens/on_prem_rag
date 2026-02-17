# Test Execution Workflow

Created: 2025-02-17
Updated: 2025-02-17

When tests run and how to run them efficiently.

## When Tests Run

| Trigger        | Fast unit | Slow | Integration (internet) |
|----------------|-----------|------|------------------------|
| Pre-push hook  | Yes       | No   | No                     |
| `uv run pytest` | Yes (default) | No | No                     |
| CI (PR/push)   | Yes       | Yes  | Yes                    |

Pre-push runs only fast tests for quick feedback. Full suite runs on CI and can be run locally before opening a PR.

## Commands

```bash
# Default (fast unit only)
uv run pytest

# Full suite (before PR)
uv run pytest -n 8 -m "" --run-internet
```

## Markers

- `slow` – performance / longer tests
- `internet` – needs network or models
- `ci_skip` – excluded on CI (run locally when needed)
- `guardrails_ci_skip` – excluded on CI (PyTorch CPU issues)

## References

- [CI_TROUBLESHOOTING.md](CI_TROUBLESHOOTING.md)
- [GIT_HOOKS.md](GIT_HOOKS.md)
