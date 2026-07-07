# Merge Strategy & Branch Cleanup

## Repository Settings

This repository is configured to enforce consistent merge behavior:

### Merge Commit Strategy

**Setting**: Enable **Merge commits**, disable Squash merging and Rebase merging.

**Location**: Repository Settings → General → Pull Requests → Merge button

**Rationale**:
- **Merge commits** preserve branch history and create clear audit trails
- Each PR gets a merge commit with the PR title and number in the message
- Enables clear `git log` history showing when features were integrated
- Supports rollback via `git revert` on the merge commit

```
Example merge commit: Merge pull request #172 from pkuppens/docs/improve-readme
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
4. **GitHub merges** with merge commit (explicit commit message)
5. **Auto-delete** removes source branch
6. **Cleanup workflow** (if needed) ensures remote sync

## Commands Reference

```bash
# Check merge strategy is working
git log --oneline | head -20  # Look for "Merge pull request" commits

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
   - ✅ Allow merge commits (keep only this checked)
   - ❌ Uncheck "Allow squash merging"
   - ❌ Uncheck "Allow rebase merging"
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
  "rebaseMergeAllowed": false,
  "squashMergeAllowed": false
}
```

## Documentation References

- **Branch Protection**: [.cursor/rules/branch-policy.mdc](../../.cursor/rules/branch-policy.mdc)
- **Merge-via-PR Skill**: [.claude/skills/merge-via-pr/SKILL.md](../../.claude/skills/merge-via-pr/SKILL.md)
- **Git Hooks**: [docs/technical/GIT_HOOKS.md](../../docs/technical/GIT_HOOKS.md)
- **Agent Guidance**: [AGENTS.md](../AGENTS.md#git-push-enforcement)
