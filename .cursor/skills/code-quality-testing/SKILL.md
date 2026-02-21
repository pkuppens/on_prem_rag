---
name: code-quality-testing
description: Apply testing efficiency and effectiveness principles. Use when writing tests, reviewing test suites, or improving test coverage. Emphasizes behavioral coverage and mutation-aware assertions.
---

# Code Quality: Testing

Tests are production code. Apply the same quality standards.

## Structure

- **Every test tests one behavior.** A failing test should tell you exactly what broke without reading the test body.
- **Test names are sentences:** `test_chunker_splits_on_sentence_boundary_not_word_boundary` is better than `test_chunker_2`.
- **Test docstrings:** "As a user I want [objective], so I can [benefit]." for user-facing tests. For technical/utility tests, use full docstring with Args/Returns or a concise one-liner. See [test-documentation.mdc](.cursor/rules/test-documentation.mdc).

## Efficiency

- **Prefer narrow, fast unit tests.** Mock external deps (Ollama, ChromaDB, auth) at the boundary — not deep inside logic.
- **Mark slow/external tests.** Any test touching network, Docker, or Ollama gets the right marker (`@pytest.mark.slow`, `@pytest.mark.ollama`, etc.).
- **Avoid duplication.** If several tests set up the same fixture with minor variations, use `@pytest.mark.parametrize`.

## Effectiveness

- **Mutation testing (mutmut) guidance:** Assert specific outcomes. An assertion that passes when the condition is inverted doesn't test anything. Each test must assert a definite result, not just "no exception raised".
- **Coverage is a floor, not a goal.** 100% coverage with weak assertions is worse than 80% with assertions that catch mutations. Prioritize behavioral coverage over line coverage.
