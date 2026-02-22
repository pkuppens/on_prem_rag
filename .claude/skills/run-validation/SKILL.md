---
name: run-validation
description: Execute an implementation validation file step by step. Runs each step, checks outcomes, marks checkboxes, diagnoses failures, fixes issues (code or validation), and reports final pass/fail. Use after implementation to verify a feature before creating a PR.
argument-hint: [#issue-number or path/to/validation.md]
---

# Run Implementation Validation

Execute the validation for $ARGUMENTS.

Parse $ARGUMENTS:
- `#NNN` or `NNN` → load `tmp/validations/issue-NNN-validation.md`
- file path → load from that path
- *(empty)* → list `tmp/validations/*.md` and ask user to select

Follow [.cursor/skills/run-validation/SKILL.md](.cursor/skills/run-validation/SKILL.md) exactly.

## Quick Reference

**Protocol** (per step, in order):
1. Execute the action (run command / navigate URL / read file)
2. Compare actual output to Expected
3. **PASS** → mark `[x]`, report "✓ Step N passed"
4. **FAIL** → diagnose root cause → fix code or correct validation → re-run
5. If still failing → mark `[!]` blocked, document blocker, continue

**On correction**: Rewrite the step's Action or Expected in the file. Add inline note:
> **Correction (YYYY-MM-DD):** [what changed and why]

Never silently change expectations to pass a failing step.

**Blocking failure**: If a prerequisite step fails and all subsequent steps depend on it, stop and report.

## Final Report Format

```
Validation: <title>
Result: PASSED / FAILED
Steps: N passed, M failed, K blocked

Failed:
- Step X: [title] — [reason]

Next steps: [fix suggestion or /commit if passed]
```

## Post-Pass Actions

1. Update `status: passed` in frontmatter
2. Check `- [ ] All steps passed` in "Overall Validation Result"
3. Suggest:
   ```bash
   gh issue comment NNN --body "Validation passed. All N steps verified."
   ```
4. Update acceptance criteria checkboxes in the GitHub issue body
5. Update `tmp/github/progress/issue-NNN-workflow.md` with validation outcome
