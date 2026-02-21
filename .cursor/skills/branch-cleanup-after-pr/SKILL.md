---
name: branch-cleanup-after-pr
description: Sync local branches after a PR is merged. Checkout main, pull, fetch --prune, delete local branches that are merged or track gone remotes. Use when a PR was just merged (merge, squash, or rebase) or when local branch list is stale.
---

# Branch Cleanup After PR Merge

When a PR is merged (merge commit, squash-merge, or rebase-merge), run this to sync local state and remove obsolete branches.

## Workflow

1. **Checkout main, pull**
   ```bash
   git checkout main
   git pull
   ```

2. **Fetch with prune** (removes refs for deleted remote branches)
   ```bash
   git fetch --prune
   ```

3. **Identify branches to delete**
   - **Merge commits**: `git branch --merged main` — branch tip is in main's history
   - **Squash/rebase**: `git branch -vv | grep ': gone]'` — remote was deleted on GitHub after merge

4. **Delete local branches**
   - From --merged list (exclude main)
   - From gone list: extract branch name, run `git branch -d <name>`

## Merge Type Coverage

| Type | Detection | Notes |
|------|-----------|-------|
| Merge commit | `--merged main` | Branch tip is ancestor of main |
| Squash merge | `: gone]` after prune | Remote branch deleted; commits not in main's history |
| Rebase merge | `: gone]` after prune | Same as squash |

## Protected Branches

Never delete: `main`, `master`, `develop`, `release/*`, `hotfix/*`

## Cross-Platform

- **PowerShell**: Use `Select-String` instead of `grep`; use `;` not `&&`
- **Bash**: Standard grep/awk/sed

## Reference

Full command: [.cursor/commands/branch-cleanup.md](.cursor/commands/branch-cleanup.md)
