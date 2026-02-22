---
name: create-validation
description: Create an implementation validation document for a feature or issue. Produces a step-by-step checklist with exact commands, URLs, and expected outcomes. Use after implementation planning or before PR creation.
argument-hint: [#issue-number or feature-slug]
---

# Create Implementation Validation

Create a validation document for $ARGUMENTS.

Parse $ARGUMENTS:
- `#NNN` or `NNN` → issue number; load from `tmp/github/issue-descriptions/issue-NNN.md` or run `gh issue view NNN`
- `for <slug>` → feature slug; save as `docs/validations/feature-<slug>-validation.md`
- *(empty)* → ask user for issue number or feature name

Follow [.cursor/skills/create-validation/SKILL.md](../../../.cursor/skills/create-validation/SKILL.md) exactly.

## Quick Reference

**Goal**: Produce a `tmp/validations/issue-NNN-validation.md` (or `docs/validations/feature-<slug>-validation.md`) where every step has:
- An exact **Action** (command or UI instruction)
- An explicit **Expected** outcome (no vague wording)
- A `- [ ] Step passed` checkbox

**Format spec**: [docs/technical/VALIDATION_FORMAT.md](../../../docs/technical/VALIDATION_FORMAT.md)

**Step types**: CLI command · HTTP request · UI browser check · file check · log check

**Quality bar**: A person who didn't write the code can execute the validation and reach the same conclusion.

## After Creating

Report:
```
Created: tmp/validations/issue-NNN-validation.md
Steps: N steps (prerequisites: X | tests: Y | API: Z | UI: W)
Run: /run-validation #NNN
```

Update `tmp/github/progress/issue-NNN-workflow.md` to reference the validation file.
