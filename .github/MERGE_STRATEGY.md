# Merge Strategy & Branch Cleanup

## Repository Settings

This repository allows two merge methods and expects the person merging to
pick the right one per PR (see [Choosing a Merge Method](#choosing-a-merge-method)
below). Squash merging stays disabled.

### Merge Methods: Rebase (default) + Merge Commit (exception)

**Setting**: Enable **Allow rebase merging** and **Allow merge commits**. Disable **Allow squash merging**.

**Location**: Repository Settings → General → Pull Requests → Merge button

**Rationale**:
- Most PRs here (chores, docs, fixes, most features) already arrive as a small
  number of well-formed, reviewed commits. Rebase merge keeps `main` linear and
  makes `git bisect`/`git blame` trace directly to the original commit — no
  synthetic merge/squash commit in the way.
- Squash is disabled because it would discard exactly the kind of deliberate,
  multi-commit history this repo writes on purpose (e.g. a refactor commit
  followed by a targeted lint-fix commit) — squashing flattens that back into
  one commit and loses the "why split this way" signal.
- Merge commits are kept available, but only for the two cases below where a
  linear rebase actively loses information or can't be produced cleanly.

### Choosing a Merge Method

**Default: rebase merge.** Use it unless one of the two exceptions below applies.

**Exception 1 — real conflicts.** If bringing the branch onto `main` requires an
actual 3-way conflict resolution (not just a mechanical `git rebase` replay),
merge instead of rebasing. Rebasing a long-diverged branch commit-by-commit can
force you to resolve the same conflict repeatedly; a merge resolves it once,
and the merge commit records that a real reconciliation happened.

**Exception 2 — a feature narrative worth preserving.** For a large,
multi-commit feature branch where the individual commits tell a meaningful
story you want visible as a unit in `git log --graph` (not just "squashed into
one PR"), use a merge commit deliberately at merge time. This is an opt-in
call made by the PR author/reviewer, not an automatic "big PR = merge commit"
rule — most large PRs still rebase cleanly and should still be rebased.

Everything else — chores, docs, dependency bumps, fixes, ordinary features —
rebases.

```
Example rebase-merged history:  ...  <commit A>  <commit B>  (from PR, now on main, linear)
Example merge-commit history:   ...  <merge commit "Merge pull request #NNN from ...">
                                        \  <commit A>  <commit B>  (branch, preserved)
```

### Automatic Branch Deletion

**Setting**: Enable "Delete head branch on merge"

**Location**: Repository Settings → General → Pull Requests

**Rationale**:
- Automatically removes feature branches after successful PR merge
- Keeps repository clean without manual cleanup
- Combined with CI/CD status checks, ensures only clean branches remain
- Reduces cognitive load and prevents stale branch confusion

## CI/CD Integration

### Branch Protection & Status Checks

The `python-ci.yml` workflow validates all PRs with:
- Unit tests (`pytest`)
- Linting (`ruff check`, `ruff format`)
- Coverage thresholds
- Pre-commit hooks

**Merge is blocked** until all status checks pass.

### Automated Cleanup (Post-Merge)

The `cleanup.yml` workflow runs after merge to:
- Delete merged branches (handles edge cases where auto-delete didn't trigger)
- Clean up old workflow runs
- Prune remote tracking references

**Triggers**: After `python-ci.yml` completes on main

## Workflow

1. **Create PR** from named branch (feature/*, docs/*, fix/*, etc.)
2. **CI/CD validates** (tests, lint, coverage)
3. **Merge approved** (requires status checks to pass)
4. **GitHub merges** — rebase by default; merge commit only for the two
   exceptions in [Choosing a Merge Method](#choosing-a-merge-method)
5. **Auto-delete** removes source branch
6. **Cleanup workflow** (if needed) ensures remote sync

## Commands Reference

```bash
# gh pr merge picks the method explicitly — there is no repo-wide default to rely on
gh pr merge <NNN> --rebase --delete-branch   # default
gh pr merge <NNN> --merge --delete-branch    # only for the two exceptions above

# Verify branch auto-delete worked
git branch -a  # Remote tracking branches cleaned automatically

# Manual cleanup if needed (local branches only)
git branch -d feature/completed-work
```

## Enforcement

- **Pre-push hook** in `scripts/setup_git_hooks.py` runs unit tests before push
- **GitHub branch protection** requires passing status checks before merge
- **No direct pushes to main** allowed — all changes via PR
- See [AGENTS.md](../AGENTS.md) for merge-via-PR requirements

## Repository Configuration

### Enable in GitHub Web UI

1. Navigate to: **Settings** → **General** → **Pull Requests**
   - ✅ Allow rebase merging (default method)
   - ✅ Allow merge commits (exception method — see above)
   - ❌ Uncheck "Allow squash merging"
   - ✅ Automatically delete head branches
   - ✅ Always suggest updating pull request branches

2. Navigate to: **Settings** → **Branches** → **Branch protection rules** (for main)
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require conversation resolution before merging
   - ✅ Require commits to be signed (optional but recommended)

### Verify via CLI

```bash
# Check current settings (requires GitHub CLI with repo permissions)
gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge
```

Expected output:
```
{
  "deleteBranchOnMerge": true,
  "mergeCommitAllowed": true,
  "rebaseMergeAllowed": true,
  "squashMergeAllowed": false
}
```

## Documentation References

- **Branch Protection**: [.cursor/rules/branch-policy.mdc](../../.cursor/rules/branch-policy.mdc)
- **Merge-via-PR Skill**: [.claude/skills/merge-via-pr/SKILL.md](../../.claude/skills/merge-via-pr/SKILL.md)
- **Git Hooks**: [docs/technical/GIT_HOOKS.md](../../docs/technical/GIT_HOOKS.md)
- **Agent Guidance**: [AGENTS.md](../AGENTS.md#git-push-enforcement)
