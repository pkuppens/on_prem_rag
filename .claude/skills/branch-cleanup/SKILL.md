# Branch Cleanup: Post-PR Merge

## Purpose

Sync local repo with remote after a PR is merged. Checks out `main`, pulls, prunes stale refs, and deletes local branches whose content is already in main — covering **merge**, **squash-merge**, and **rebase-merge**.

## Redirect To (do not duplicate)

- **PR creation**: Use `/pr` when ready to merge. Run this command **after** the PR is merged.
- **Script**: [scripts/cleanup-merged-branches.sh](scripts/cleanup-merged-branches.sh) for CI/automated cleanup (merge commits only).

## When to Use

- After merging a PR (locally or via GitHub UI)
- When switching to a new issue and local branches are stale
- Periodically to keep branch list manageable

## Merge Detection Strategy

| Merge type | Detection | How |
|------------|-----------|-----|
| **Merge commit** | Branch tip is ancestor of main | `git branch --merged main` |
| **Squash merge** | Remote branch deleted on GitHub | `git branch -vv \| grep ': gone]'` after `git fetch --prune` |
| **Rebase merge** | Same as squash | Remote deleted after merge |

**Note**: Squash and rebase rewrites commits, so `--merged` does not match. When the PR is merged on GitHub, the remote branch is usually deleted. After `git fetch --prune`, such branches show `[origin/branch: gone]`.

## Prerequisites

- Git repository with `main` (or `master`) as default branch
- No uncommitted work that would be lost, or run `git stash` first
- PowerShell users: Use `;` instead of `&&` for chained commands

## Command Execution Workflow

### Step 1: Check Working Tree

```bash
git status
```

**If dirty** (uncommitted changes): Stash or commit before switching. Ask user to `git stash` or commit first.

### Step 2: Checkout Main and Pull

```bash
git checkout main
git pull
```

### Step 3: Fetch and Prune

```bash
git fetch --prune
```

Removes remote-tracking refs for branches deleted on the remote (e.g. after squash/rebase merge).

### Step 4: Identify Branches to Delete

**Protected** (never delete): `main`, `master`, `develop`, `release/*`, `hotfix/*`

**Candidates for deletion**:

1. **Merged into main** (merge commits):
   ```bash
   git branch --merged main
   ```
   Exclude `main` and current branch.

2. **Track deleted remote** (squash/rebase merge):
   ```bash
   git branch -vv | grep ': gone]'
   ```
   Extract branch name (first column; trim leading `*` and spaces).

**PowerShell** (for gone branches):
```powershell
git branch -vv | Select-String ': gone\]' | ForEach-Object {
  ($_ -replace '^\*?\s+', '').Split([char[]]@(' ', '['))[0]
}
```

**Bash/Unix**:
```bash
git branch -vv | grep ': gone]' | awk '{print $1}' | sed 's/^[* ]*//'
```

### Step 5: Delete Branches

**Dry-run (default)**: List branches that would be deleted. Do not delete.

**Execute**: Delete with `git branch -d <branch>`. Use `-D` only if user explicitly requests force-delete.

```bash
# Example (after identifying branches)
git branch -d feature/118-testing-strategy-redesign
```

### Step 6: Optional — Run Existing Script

For automated cleanup (merge commits + remote), you can run:

```bash
bash scripts/cleanup-merged-branches.sh        # Dry-run
bash scripts/cleanup-merged-branches.sh --execute --local-only  # Execute local only
```

**Limitation**: The script uses `--merged` only; it does not delete local branches that track gone remotes (squash/rebase). This command covers both.

## Usage Examples

### Example 1: Full cleanup (dry-run)

```bash
git checkout main
git pull
git fetch --prune
# List merged + gone branches
git branch --merged main
git branch -vv | grep ': gone]'
# Report what would be deleted; do not delete
```

### Example 2: Delete gone branches after squash-merge

```bash
git checkout main
git pull
git fetch --prune
# Delete locals tracking gone remote
git branch -vv | grep ': gone]' | awk '{print $1}' | sed 's/^[* ]*//' | while read b; do
  [ -n "$b" ] && [ "$b" != "main" ] && git branch -d "$b"
done
```

## Error Handling

| Condition | Action |
|-----------|--------|
| Working tree dirty | Warn; suggest `git stash` or commit first |
| Not in git repo | Report error |
| `main` does not exist | Try `master`; report if neither exists |
| Branch delete fails (`-d` refuses) | Report; suggest `-D` only if user confirms |
| PowerShell: `grep` not found | Use `Select-String` or `findstr` |

## Success Criteria

- Local `main` is up to date with `origin/main`
- Stale remote-tracking refs pruned
- Merged/gone local branches deleted (or listed in dry-run)
- User informed of what was deleted or would be deleted

## References

- [scripts/cleanup-merged-branches.sh](scripts/cleanup-merged-branches.sh) — Merge-based cleanup (CI)
- [branch-policy.mdc](.cursor/rules/branch-policy.mdc) — Branch naming
- [github-integration.mdc](.cursor/rules/github-integration.mdc) — gh CLI patterns
