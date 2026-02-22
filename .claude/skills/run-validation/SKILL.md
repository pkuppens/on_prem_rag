---
name: run-validation
description: Execute an implementation validation file step by step. Runs each step, checks outcomes, marks checkboxes, diagnoses failures, fixes issues (code or validation), and reports final pass/fail. Use after implementation to verify a feature before creating a PR.
argument-hint: [#issue-number or path/to/validation.md]
---

# Run Implementation Validation

Execute the validation for $ARGUMENTS.

Parse $ARGUMENTS:
- `#NNN` or `NNN` → load `tmp/github/issue-NNN/validation.md`
- file path → load from that path
- *(empty)* → list `tmp/github/issue-*/validation.md` and ask user to select

Follow [.cursor/skills/run-validation/SKILL.md](../../../.cursor/skills/run-validation/SKILL.md) exactly.
