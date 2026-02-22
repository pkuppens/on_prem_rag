---
name: create-validation
description: Create an implementation validation document for a feature or issue. Produces a step-by-step checklist with exact commands, URLs, and expected outcomes. Use after implementation planning or before PR creation to define how the feature can be verified end-to-end.
---

# Create Implementation Validation

A validation document proves an implementation is complete. It is executable: each step is a concrete action (command, URL, UI check) with an explicit expected outcome.

## When to Use

- After Phase 2 (Plan) is complete — create the validation so it guides Phase 3 implementation
- Before creating a PR — validate your implementation against the spec
- When writing acceptance criteria that must be verified, not just asserted

## Format Reference

See [docs/technical/VALIDATION_FORMAT.md](../../docs/technical/VALIDATION_FORMAT.md) for the full schema and example steps.

## Storage

| Scope | Location |
|-------|----------|
| Session-scoped (ephemeral) | `tmp/validations/issue-NNN-validation.md` |
| Feature-scoped (committed) | `docs/validations/feature-<slug>-validation.md` |

Default to `tmp/validations/` unless the user asks for a committed validation.

## How to Create a Validation

### 1. Gather Context

Read:
- The issue acceptance criteria (`gh issue view NNN` or `tmp/github/issue-descriptions/issue-NNN.md`)
- The implementation plan (`tmp/github/progress/issue-NNN-plan.md`)
- Relevant API docs, service ports (`docs/PORTS.md`), and entry point commands (CLAUDE.md)

### 2. Identify Validation Steps

Map each acceptance criterion to one or more verifiable steps. Ask:

- **Does it run?** → unit/integration test command
- **Does the API respond correctly?** → curl command with expected status + body
- **Is the UI visible/functional?** → browser URL + element description
- **Does it log correctly?** → log tail command + expected pattern
- **Does it integrate with other services?** → end-to-end scenario

### 3. Write Steps

Each step must have:

- **Action**: exact command (`uv run pytest ...`, `curl -X POST ...`) or exact UI instruction ("Browse to `http://localhost:PORT/path`; click `Submit`")
- **Expected**: explicit outcome ("Exit code 0; output contains `3 passed`" — not "it works")
- **Checkbox**: `- [ ] Step passed`
- **Optional note**: troubleshooting hint if step commonly fails for environmental reasons

**Step ordering**: simple → complex; unit → integration → end-to-end. Each step may assume prior steps passed.

### 4. Write Prerequisites

List what must be running/configured before the first step. Include the exact commands to start services.

### 5. Write the Goal

One sentence: "This validation asserts that [feature] is implemented correctly by verifying [key behaviors]."

### 6. Save the File

Write to `tmp/validations/issue-NNN-validation.md` using the format template in VALIDATION_FORMAT.md.

Update `tmp/github/progress/issue-NNN-workflow.md` to reference the validation file.

## Quality Bar for Validations

A good validation:
- Can be executed by someone who didn't write the code
- Has zero ambiguous expectations ("visible", "works", "correct" are banned without specifics)
- Covers the critical path of the acceptance criteria, not every edge case
- Each step is independently verifiable (one action, one assertion)

## Example Step (Good vs Bad)

**Bad:**
```
### Step 2: Test upload
Action: Upload a file.
Expected: Works correctly.
- [ ] Step passed
```

**Good:**
```
### Step 2: Upload PDF via API

**Action:** Run:
```bash
curl -s -X POST http://localhost:9180/upload \
  -F "file=@tests/fixtures/sample.pdf" | jq .
```

**Expected:** HTTP 200. JSON response contains `"status": "success"` and a non-empty `"document_id"` field.

- [ ] Step passed
```

## References

- [docs/technical/VALIDATION_FORMAT.md](../../docs/technical/VALIDATION_FORMAT.md) — full format spec
- [docs/PORTS.md](../../docs/PORTS.md) — service ports
- [CLAUDE.md](../../CLAUDE.md) — build/run commands
- [.cursor/skills/run-validation/SKILL.md](../run-validation/SKILL.md) — executes and verifies a validation file
