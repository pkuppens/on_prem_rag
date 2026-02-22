# Implementation Validation Format

This document defines the format for implementation validation files used across the project.

Validation files are stored in `tmp/validations/` (gitignored, per-session) or in `docs/validations/` for persistent, committed validations tied to features.

## File Naming

```
tmp/validations/issue-NNN-validation.md        # Per-issue, session-scoped
docs/validations/feature-<slug>-validation.md  # Committed, feature-scoped
```

## Validation Document Structure

```markdown
---
issue: NNN
feature: Short feature name
created: YYYY-MM-DD
status: pending | in-progress | passed | failed
---

# Validation: <Feature or Issue Title>

## Goal

One sentence: what this validation asserts and why it proves the implementation is complete.

## Prerequisites

List anything that must be true before starting validation:
- [ ] Service X is running (`uv run start-backend`)
- [ ] Docker stack up (`docker-compose up -d`)
- [ ] Environment variable Y is set

## Steps

Each step has:
- A **what to do** instruction (exact command or UI action)
- An **expected outcome** (what success looks like)
- A checkbox to track progress
- Optional `> [!NOTE]` for context or troubleshooting hints

Steps are sequential: each step may assume all prior steps passed.

---

### Step 1: <Short title>

**Action:** Run the following command:
```bash
uv run pytest tests/test_feature.py -v
```

**Expected:** All tests pass. Output ends with `X passed` (no failures or errors).

- [ ] Step passed

---

### Step 2: <Short title>

**Action:** Browse to `http://localhost:9180/docs` and expand the `POST /upload` endpoint.

**Expected:** The endpoint is visible, and its request body schema shows a `file` field of type `string (binary)`.

- [ ] Step passed

> [!NOTE]
> If the docs page returns 404, the backend is not running. Run `uv run start-backend` and retry.

---

### Step 3: <Short title>

**Action:** Upload a sample PDF using the API:
```bash
curl -X POST http://localhost:9180/upload \
  -F "file=@tests/fixtures/sample.pdf"
```

**Expected:** Response is HTTP 200 with JSON `{"status": "success", "document_id": "<uuid>"}`.

- [ ] Step passed

---

## Overall Validation Result

- [ ] All steps passed
- [ ] Implementation is complete per acceptance criteria

**Notes / Issues Found:**
<!-- Document any failures here. The run-validation skill will update this section. -->
```

## Step Types

| Type | Format |
|------|--------|
| CLI command | Code block with exact command; expected = stdout/stderr pattern or exit code |
| HTTP request | `curl` or browser URL; expected = status code + response body |
| UI interaction | Browser URL + action description; expected = visible element or text |
| File check | Path to check + expected content or existence |
| Log check | Command to tail log; expected = log line pattern |

## Expectations Wording

Be explicit. Vague expectations fail silently. Use:

| Instead of | Use |
|-----------|-----|
| "It works" | "Response is HTTP 200 with `{"status": "ok"}`" |
| "No errors" | "Exit code 0; no lines containing `ERROR` in output" |
| "UI looks right" | "The `Upload` button is visible and clickable on `http://localhost:3000`" |
| "Tests pass" | "`uv run pytest` exits 0; output contains `X passed, 0 failed`" |

## Flow Invariant

**Each step assumes all prior steps have passed.** Do not design steps that are valid even if a prior step failed. If step 3 requires step 2's artifact, state that dependency explicitly in the step's Action or Note.
