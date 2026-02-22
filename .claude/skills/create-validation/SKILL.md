---
name: create-validation
description: Create an implementation validation document for a feature or issue. Produces a step-by-step checklist with exact commands, URLs, and expected outcomes. Use after implementation planning or before PR creation.
argument-hint: [#issue-number or feature-slug]
---

# Create Implementation Validation

Create a validation document for $ARGUMENTS.

Parse $ARGUMENTS:
- `#NNN` or `NNN` → issue number; load from `tmp/github/issue-NNN/description.md` or run `gh issue view NNN`
- `for <slug>` → feature slug; save as `docs/validations/feature-<slug>-validation.md`
- *(empty)* → ask user for issue number or feature name

Follow [.cursor/skills/create-validation/SKILL.md](../../../.cursor/skills/create-validation/SKILL.md) exactly.
