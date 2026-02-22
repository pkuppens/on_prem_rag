# Cursor Commands

Commands are invoked with `/command-name`. Use **delegation** for reuse; keep the flow **acyclic**.

## Workflow Flow (acyclic)

```
/get-started  →  /create-validation  →  (work)  →  /run-validation  →  /commit  →  /pr  →  /branch-cleanup
   ↓                   ↓                                  ↓                ↓           ↑
   entry for issues    define how to verify          verify + fix     gate on pass  prereqs done
```

- **get-started**: Entry for issue work. Suggests `/create-validation`, `/commit`, `/pr` as next steps.
- **create-validation**: After planning — define verification steps before or during implementation.
- **run-validation**: After implementation — execute validation, fix failures, gate PR on pass.
- **commit**: Create commits. Suggests `/pr` when ready.
- **pr**: Create PR. Prerequisites: all changes committed; validation passed.
- **branch-cleanup**: After PR is merged. Sync main, prune refs, delete merged/gone local branches.

## Commands

| Command | Purpose | Next / Uses |
|---------|---------|-------------|
| `/get-started` | Issue workflow (Validate → Plan → Implement) | `/create-validation`, `/commit`, `/pr` when ready |
| `/create-validation` | Create step-by-step validation document for a feature/issue | `/run-validation` after implementation |
| `/run-validation` | Execute validation, check/fix steps, report pass/fail | `/commit` when passed; fix when failed |
| `/commit` | Create commits with quality checks | `/pr` when ready; [commit-message-standards](.cursor/rules/commit-message-standards.mdc) |
| `/pr` | Create pull request | Prereq: commits done; validation passed |
| `/branch-cleanup` | Sync local branches after PR merged (main, prune, delete merged/gone) | After `/pr` merge; merge/squash/rebase |
| `/test` | Run tests with service management | Used by commit (require tests), pr (pre-flight) |
| `/update-commits` | WBSO: refresh commit CSVs from `repositories.csv` | Standalone |
| `/update-date-tags` | Update Created/Updated tags in files | [date-formatting](.cursor/rules/date-formatting.mdc) |

## Rules

- [temp-files.mdc](.cursor/rules/temp-files.mdc) — tmp/ structure; used by get-started, commit, pr
- [commit-message-standards.mdc](.cursor/rules/commit-message-standards.mdc) — commit format; executed by commit command
- [github-integration.mdc](.cursor/rules/github-integration.mdc) — gh patterns; referenced by get-started, pr

## Validation Format

- [docs/technical/VALIDATION_FORMAT.md](../../docs/technical/VALIDATION_FORMAT.md) — schema for validation files created by `/create-validation` and consumed by `/run-validation`
- Storage: `tmp/validations/issue-NNN-validation.md` (session-scoped) or `docs/validations/feature-<slug>-validation.md` (committed)
