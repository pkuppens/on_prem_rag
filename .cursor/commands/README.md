# Cursor Commands

Commands are invoked with `/command-name`. Use **delegation** for reuse; keep the flow **acyclic**.

## Workflow Flow (acyclic)

```
/get-started  →  (work)  →  /commit  →  (repeat)  →  /pr  →  (merge)  →  /branch-cleanup
   ↓                              ↓                    ↑                    ↑
   entry for issues         next step when ready    prerequisites:     after PR merged
                           for PR                   commits done
```

- **get-started**: Entry for issue work. Suggests `/commit` and `/pr` as next steps.
- **commit**: Create commits. Suggests `/pr` when ready. Errors if nothing to commit (no delegation to get-started).
- **pr**: Create PR. Prerequisites: all changes committed; if issue workflow, get-started was used earlier. References commit's quality checks; does not invoke commit.
- **branch-cleanup**: After PR is merged. Sync main, prune refs, delete merged/gone local branches (merge, squash, rebase).

## Commands

| Command | Purpose | Next / Uses |
|---------|---------|-------------|
| `/get-started` | Issue workflow (Validate → Plan → Implement) | `/commit`, `/pr` when ready |
| `/commit` | Create commits with quality checks | `/pr` when ready; [commit-message-standards](.cursor/rules/commit-message-standards.mdc) |
| `/pr` | Create pull request | Prereq: commits done; uses commit's quality gates |
| `/branch-cleanup` | Sync local branches after PR merged (main, prune, delete merged/gone) | After `/pr` merge; merge/squash/rebase |
| `/test` | Run tests with service management | Used by commit (require tests), pr (pre-flight) |
| `/update-commits` | WBSO: refresh commit CSVs from `repositories.csv` | Standalone |
| `/update-date-tags` | Update Created/Updated tags in files | [date-formatting](.cursor/rules/date-formatting.mdc) |

## Rules

- [temp-files.mdc](.cursor/rules/temp-files.mdc) — tmp/ structure; used by get-started, commit, pr
- [commit-message-standards.mdc](.cursor/rules/commit-message-standards.mdc) — commit format; executed by commit command
- [github-integration.mdc](.cursor/rules/github-integration.mdc) — gh patterns; referenced by get-started, pr
