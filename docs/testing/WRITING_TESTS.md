# Writing Tests

Created: 2026-02-20

## Quick Start

1. **Pick the right directory** (see [TEST_STRATEGY.md](TEST_STRATEGY.md)):
   - `tests/unit/core/` for chunking, document_loader, embeddings logic
   - `tests/unit/backend/` for memory, guardrails, etc.
   - `tests/` (root) for now—new tests should migrate to unit/integration/performance

2. **Add the right marker**:
   - Default: no marker (unit, fast)
   - `@pytest.mark.slow` if the test takes >5s or loads models
   - `@pytest.mark.internet` if it needs network
   - `@pytest.mark.ollama` if it needs a local Ollama instance

3. **Use light data for unit tests**:
   - Prefer small fixtures or synthetic data
   - Use `2005.11401v4.pdf` instead of `2303.18223v16.pdf` when a real PDF is needed

## Docstring Format

See [.cursor/rules/test-documentation.mdc](../../.cursor/rules/test-documentation.mdc).

```python
def test_example(self):
    """As a user I want [objective], so I can [benefit].
    Technical: [requirement].
    """
```

## Fixture Scope

- **session**: Immutable resources (config, read-only data)
- **module**: Per-file (e.g. DB, model loaded once per file)
- **function**: Default when state is mutable

## Markers Reference

| Marker               | When to use                                 |
| -------------------- | ------------------------------------------- |
| (none)               | Fast unit test                              |
| `slow`               | >5s or model loading                        |
| `internet`           | Network required                            |
| `ollama`             | Ollama on port 11434                        |
| `docker`             | Full Docker stack                           |
| `guardrails_ci_skip` | PyTorch/guardrails; skip on some CI runners |
| `ci_skip`            | Missing models or resources on CI           |

## Layout Convention

New tests should go in `tests/unit/<area>/` or `tests/integration/` to mirror `src/`. Flat `tests/test_*.py` is legacy; migrate when touching a file.
