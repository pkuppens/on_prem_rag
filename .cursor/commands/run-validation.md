# Run Implementation Validation

## Purpose

Execute a validation document step by step. For each step: run the command or check the UI, compare to the expected outcome, check off passing steps, diagnose and fix failures, and update the validation with corrections.

## Redirect To (do not duplicate)

- **Creating a validation**: Use `/create-validation` to generate the validation document first
- **Validation format**: [docs/technical/VALIDATION_FORMAT.md](../docs/technical/VALIDATION_FORMAT.md)
- **Committing and PRs**: Use `/commit` and `/pr` after validation passes

## When to Use

- After implementing a feature — gate PR on passing validation
- During development — verify partial progress
- Re-run after fixing a failed step

## Input Parsing

| Pattern | Action |
|---------|--------|
| `#NNN` or `issue NNN` | Load `tmp/validations/issue-NNN-validation.md` |
| File path | Load validation from that path |
| *(empty)* | List `tmp/validations/*.md`, ask user to select |

## Execution

Follow [.cursor/skills/run-validation/SKILL.md](../skills/run-validation/SKILL.md) exactly.

**Summary:**
1. Load validation file; report steps and current state
2. Execute each unchecked step in order
3. On pass → check off `[x]`; on fail → diagnose, fix, re-run
4. Correct the validation file when a step or expectation was wrong (with inline note explaining why)
5. After all steps: update `status` frontmatter, fill "Overall Validation Result"
6. Report: N passed / M failed / K blocked

## Output

```
Validation: <title>
Result: PASSED / FAILED
Steps: N passed, M failed, K blocked
[list of failed/blocked steps with reason]

Next: /commit  (if passed)
Next: fix <specific issue>  (if failed)
```

## On Validation Pass

Suggest:
```bash
gh issue comment NNN --body "Validation passed. All N steps verified."
```
And update acceptance criteria checkboxes in the issue body.
