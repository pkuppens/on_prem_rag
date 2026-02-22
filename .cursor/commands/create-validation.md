# Create Implementation Validation

## Purpose

Create a step-by-step validation document for a feature or issue. Each step is a concrete action (CLI command, URL, UI check) with an explicit expected outcome and a checkbox to track progress.

## Redirect To (do not duplicate)

- **Running the validation**: Use `/run-validation` to execute a validation document
- **Validation format**: [docs/technical/VALIDATION_FORMAT.md](../../docs/technical/VALIDATION_FORMAT.md)
- **Issue workflow**: Use `/get-started` for the full Validate → Plan → Implement flow

## When to Use

- After Phase 2 planning — define validation before implementation (TDD for integration)
- Before PR creation — codify how the feature is verified
- When acceptance criteria need executable proof of completion

## Input Parsing

The user may append text after `/create-validation`. Parse:

| Pattern | Extracted | Example |
|---------|-----------|---------|
| `#NNN` or `issue NNN` | Issue number → load from `tmp/github/issue-descriptions/issue-NNN.md` | `/create-validation #82` |
| `for <feature>` | Feature slug → save as `docs/validations/feature-<slug>-validation.md` | `/create-validation for document-upload` |
| *(empty)* | Interactive — ask for issue number or feature name | `/create-validation` |

## Storage

- Default: `tmp/validations/issue-NNN-validation.md` (gitignored, session-scoped)
- Use `docs/validations/` only when explicitly requested by user (committed, permanent)

## Execution

Follow [.cursor/skills/create-validation/SKILL.md](../skills/create-validation/SKILL.md) exactly.

**Summary:**
1. Read issue/plan context (acceptance criteria, implementation plan, ports, commands)
2. Map each acceptance criterion to verifiable steps (test, API, UI, file, log)
3. Write steps with exact commands and explicit expected outcomes
4. Write prerequisites
5. Save to `tmp/validations/issue-NNN-validation.md`
6. Update `tmp/github/progress/issue-NNN-workflow.md` to reference the validation

## Output

```
Created: tmp/validations/issue-NNN-validation.md
Steps: N (prerequisites + X test + Y API + Z UI)
Run with: /run-validation #NNN
```
