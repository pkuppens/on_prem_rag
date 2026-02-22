# Cursor Commands

Commands are invoked with `/command-name`. Use **delegation** for reuse; keep the flow **acyclic**.

## Issue Workflow

Working on a GitHub issue follows this lifecycle:

```
Phase 1: Analyse
  - Is the issue still valid? Already implemented?
  - Search codebase, git log, merged PRs for duplicates
  - Identify 2-3 solution directions; pick the best one
  - Refine acceptance criteria and fill missing detail
  - Post refinement comment to GitHub issue

Phase 2: Plan
  - Create branch from base
  - Break down into tasks; decide test strategy
  - Define how implementation will be validated
  - Post plan comment to GitHub issue

Phase 3: Implement
  - Work in small increments; commit after each
  - Run tests after each logical change
  - Keep tmp/github/issue-NNN/workflow.md updated so sessions can resume

Phase 4: Validate
  - Run /create-validation to define verification steps (can be done in Phase 2 for TDD)
  - Run /run-validation to execute; fix failures; gate PR on pass

Phase 5: PR and merge
  - /commit → /pr (base: correct branch; title references issue)
  - Merge after review; /branch-cleanup
```

### Commands per Phase

```
/get-started  ──────────────────────────────────────────────────────────────────────┐
   Phase 1: Analyse (validate issue, find duplicates, refine)                       │
   Phase 2: Plan (branch, break down, test strategy)                                │
   Phase 3: Implement (incremental commits, tests, session continuity)              │
        │                                                                            │
        ├── /create-validation  (Phase 2 or 3 — define verification steps)          │
        │         │                                                                  │
        │         └── /run-validation  (Phase 4 — execute, fix, report pass/fail)   │
        │                   │                                                        │
        └───────────────────┴── /commit ── /pr ── /branch-cleanup ──────────────────┘
```

### Issue-Validation vs Implementation-Validation

Two distinct validation activities exist — do not conflate them:

| | **Issue validation** (Phase 1) | **Implementation validation** (Phase 4) |
|---|---|---|
| **Purpose** | Is this issue worth doing? | Is the implementation correct? |
| **When** | Before writing any code | After implementation (or TDD: before) |
| **Output** | Decision: proceed / close / redirect | Pass/fail validation document |
| **Tool** | `/get-started` Phase 1 analysis | `/create-validation` + `/run-validation` |
| **Stored in** | `tmp/github/issue-NNN/workflow.md` | `tmp/github/issue-NNN/validation.md` |

`/create-validation` can be run in Phase 2 (before implementation) to define acceptance criteria as executable steps — this is the TDD approach. Or it can be run in Phase 4 after implementation to codify what was built. Both are valid.

## Commands

| Command | Purpose | Next / Uses |
|---------|---------|-------------|
| `/get-started` | Full issue lifecycle: Analyse → Plan → Implement | `/create-validation`, `/commit`, `/pr` |
| `/create-validation` | Create executable validation document for issue or feature | `/run-validation` |
| `/run-validation` | Execute validation step-by-step, fix failures, gate on pass | `/commit` when passed |
| `/commit` | Create commits with quality checks | `/pr` when ready |
| `/pr` | Create pull request | Prereq: commits done; validation passed |
| `/branch-cleanup` | Sync local branches after PR merged (main, prune, delete merged/gone) | After `/pr` merge |
| `/test` | Run tests with service management | Used by commit, pr |
| `/update-commits` | WBSO: refresh commit CSVs from `repositories.csv` | Standalone |
| `/update-date-tags` | Update Created/Updated tags in files | Standalone |

## Scratch Files

All issue scratch files live under `tmp/github/issue-NNN/`:

| File | Purpose |
|------|---------|
| `description.md` | Cached issue body (`gh issue view NNN`) |
| `workflow.md` | Phase tracking, decisions, validation outcomes, next steps |
| `plan.md` | Implementation plan (Phase 2) |
| `validation.md` | Validation document (created by `/create-validation`) |
| `comments/` | Draft comments before posting (refinement, plan, milestone, close) |

See `tmp/CLAUDE.md` for the full scratch directory rules.

## Rules

- [temp-files.mdc](.cursor/rules/temp-files.mdc) — tmp/ structure; used by get-started, commit, pr
- [commit-message-standards.mdc](.cursor/rules/commit-message-standards.mdc) — commit format; executed by commit command
- [github-integration.mdc](.cursor/rules/github-integration.mdc) — gh patterns; referenced by get-started, pr

## Validation Format

- [docs/technical/VALIDATION_FORMAT.md](../../docs/technical/VALIDATION_FORMAT.md) — schema for validation files created by `/create-validation` and consumed by `/run-validation`
- Storage: `tmp/github/issue-NNN/validation.md` (issue-scoped) or `docs/validations/feature-<slug>-validation.md` (committed)
