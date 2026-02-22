---
name: run-validation
description: Execute an implementation validation file step by step. For each step, run the command or check the UI, compare to the expected outcome, check off passing steps, and document failures. When a step fails, attempt to diagnose and fix the issue, then update the validation with corrected steps or expectations. Use after implementation to verify a feature is complete.
---

# Run Implementation Validation

Reads a validation file, executes each step, tracks pass/fail, and iterates on failures.

## When to Use

- After completing implementation of a feature or issue
- Before creating a PR — gate on all steps passing
- During development — run partial validations to check work-in-progress

## Inputs

The user provides one of:
- An issue number (`#NNN`) → look for `tmp/github/issue-NNN/validation.md`
- A file path → read validation from that path
- Nothing → list `tmp/github/issue-*/validation.md` files and ask user to select

## Execution Protocol

### Phase 1: Load Validation

1. Read the validation file
2. Check the `status` frontmatter — if `passed`, ask user if re-run is intended
3. List all steps and their current checkbox state
4. Report: "Running validation for: [title]. N steps, M already checked."

### Phase 2: Execute Steps Sequentially

For each unchecked step (in order):

#### 2a. Execute the Action

- **CLI command**: Run it. Capture stdout, stderr, exit code.
- **HTTP request**: Run `curl -s -w "\n%{http_code}"` variant. Capture body + status code.
- **UI check**: Navigate to the URL using browser tools. Capture snapshot.
- **File check**: Read the file or run `ls`/`cat` as appropriate.
- **Log check**: Run the log command. Capture relevant lines.

#### 2b. Compare to Expected

Compare actual output to the expected outcome in the step. Determine: **PASS** or **FAIL**.

- **PASS**: Update the checkbox to `[x]` in the file. Report: "✓ Step N: [title] — passed."
- **FAIL**: Report: "✗ Step N: [title] — FAILED." Include actual vs expected diff.

#### 2c. On Failure — Diagnose and Fix

When a step fails:

1. **Diagnose**: Identify root cause. Is it:
   - Implementation missing/incorrect?
   - Service not running (environmental)?
   - Wrong expected output in the validation (expectation was wrong)?
   - Wrong command in the validation (step is outdated)?

2. **Fix if possible**:
   - **Implementation bug**: Fix the code. Re-run the step after the fix.
   - **Service not running**: Start the service. Re-run the step.
   - **Wrong expectation**: Correct the expected outcome in the validation file (document why).
   - **Wrong command**: Correct the command in the validation file (document why).

3. **Update the validation file**:
   - If the step text was corrected: rewrite the step's Action or Expected block
   - If an issue was found in implementation: add a note under the step:
     ```
     > **Issue found:** [description of the bug and fix applied]
     ```
   - If environmental (not a code bug): add or update a `> [!NOTE]` block with the fix

4. **Re-run** the corrected step. If it passes now, check it off.

5. **If still failing after fix attempt**: mark the step with `[!]` (blocked), document the blocker, and move to the next step. Report at the end.

#### 2d. Blocking Failures

If a step is **prerequisite** to all subsequent steps (e.g., service won't start), stop and report:
- "Blocked at Step N: [title]. Cannot continue. Fix this before re-running."
- Update `status` in frontmatter to `failed`.

### Phase 3: Final Report

After all steps are processed:

1. Count: passed / failed / blocked
2. Update the `status` frontmatter:
   - All passed → `passed`
   - Any blocked/failed → `failed`
3. Fill in the "Overall Validation Result" section:
   - Check `- [ ] All steps passed` if all did
   - Document issues in "Notes / Issues Found"
4. Report summary:
   ```
   Validation: <title>
   Result: PASSED / FAILED
   Steps: N passed, M failed, K blocked
   [list of failed/blocked steps with brief reason]
   ```

### Phase 4: Post-Validation Actions

- **If passed**: Suggest `gh issue comment NNN --body "Validation passed. All N steps verified."` and update acceptance criteria checkboxes in the issue.
- **If failed**: Suggest next actions (fix specific steps, re-run with `/run-validation`).
- Update `tmp/github/issue-NNN/workflow.md` with validation outcome.

## Updating the Validation File

When correcting a step, preserve the original intent. Use this pattern:

```markdown
### Step 3: Upload PDF via API

**Action:** Run:
```bash
curl -s -X POST http://localhost:9180/upload \
  -F "file=@tests/fixtures/sample.pdf" | jq .
```

**Expected:** HTTP 200. JSON response contains `"status": "success"` and a non-empty `"document_id"` field.

> **Correction (2026-02-22):** Original expected `"id"` field; actual field name is `"document_id"`. Updated to match implementation.

- [x] Step passed
```

Never silently change expectations to make a failing step pass without documenting the change.

## Rules

- **Never skip a step** — sequential flow is invariant; later steps may depend on earlier ones
- **Never mark a step passed** without actually executing and verifying it
- **Always document** why an expectation was corrected (wrong spec vs wrong implementation)
- **Fix implementation first** — only correct the validation expectation if the implementation is definitively correct and the spec was wrong

## References

- [docs/technical/VALIDATION_FORMAT.md](../../../docs/technical/VALIDATION_FORMAT.md) — validation file format
- [.cursor/skills/create-validation/SKILL.md](../create-validation/SKILL.md) — creates validation files
- [CLAUDE.md](../../../CLAUDE.md) — service start commands, ports
- [docs/PORTS.md](../../../docs/PORTS.md) — service ports reference
