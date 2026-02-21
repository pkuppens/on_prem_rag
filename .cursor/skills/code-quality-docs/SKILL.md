---
name: code-quality-docs
description: Apply comment and documentation standards for Python code. Use when writing docstrings, adding comments, or marking technical debt (TODOs). Ensures explain-why-not-what and traceable debt.
---

# Code Quality: Documentation and Comments

Comments explain **why**, not **what**. Code should be self-documenting.

## Docstrings

- **Write the docstring before implementation.** If you can't summarize in one sentence, the design isn't clear yet.
- **Complete docstrings for public/core functions:** Args, Returns, Raises, and examples for complex functions. See [function-definitions.mdc](.cursor/rules/function-definitions.mdc).
- **Explain non-obvious decisions.** If a chunk size, threshold, or algorithm was chosen for a specific reason (benchmark, compliance, Ollama limitation), document it.

## Comments

- **Don't comment what the code already says.** `# increment counter` above `count += 1` is noise. Delete it.
- **Explain why** when the reason isn't obvious from code alone.

## Technical Debt (TODOs)

- **Prefer task reference:** `# TODO(TASK-NNN): Add retry logic for embedding failures`
- **Alternative:** High-quality SMART description when no task exists yet: unambiguous, clear, actionable. Example: `# TODO: Add exponential backoff when Ollama returns 503 — retry 3x with 1s, 2s, 4s delays`

Never use a bare `# TODO` without either a task ID or a complete, self-contained description.
