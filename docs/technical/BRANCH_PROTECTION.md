# Branch Protection Rules

This document outlines the recommended branch protection rules for the `main` branch to ensure code quality and prevent accidental breakages.

## Recommended Settings for `main` Branch

### Enable Branch Protection

Navigate to: **Settings** → **Branches** → **Add branch protection rule**

Branch name pattern: `main`

### Required Settings

#### ✅ Require a pull request before merging
- [x] **Require approvals**: At least 1 approval
  - Note: For solo developer projects, this can be a maintainer's self-approval before merging
- [x] **Dismiss stale pull request approvals when new commits are pushed**
  - This ensures reviews are current and reflect the latest code changes
- [x] **Require review from Code Owners** (if CODEOWNERS file exists)
  - See below for CODEOWNERS setup

#### ✅ Require status checks to pass before merging
- [x] **Require branches to be up to date before merging**
- Required status checks:
  - `setup` (Python CI)
  - `lint` (Python CI)
  - `test-unit` (Python CI)
  - `security` (Python CI)
  - `ci-summary` (Python CI)

#### ✅ Require conversation resolution before merging
- [x] **Require conversation resolution before merging**: All review comments must be resolved

#### ✅ Do not allow bypassing the above settings
- [x] **Do not allow bypassing the above settings**: Enforce for administrators

### Optional but Recommended

#### Linear history
- [x] **Require linear history**: Enforce clean git history with rebase or squash merges
  - Recommended: Use squash merges for feature branches
  - Before merging, ensure your branch is rebased on the latest main:
    ```bash
    git checkout main
    git pull
    git checkout feature/your-branch
    git rebase main
    # Resolve any conflicts
    git push --force-with-lease
    ```

#### Force push restrictions
- [x] **Restrict who can push to matching branches**: Prevent force pushes and branch deletion
  - Add administrators and trusted maintainers to the allowlist if needed

### Not Recommended

#### ❌ Require signed commits
- Unless your organization requires GPG signing, this adds friction without significant benefit for this project

#### ❌ Require deployments to succeed before merging
- Not applicable unless you have a staging environment with automated deployments

## Applying Branch Protection Rules

### Step 1: Create CODEOWNERS File

Create a `.github/CODEOWNERS` file to specify code ownership:

```
# CODEOWNERS file - defines individuals or teams responsible for code review
# Docs: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

# Default owner for everything in the repo
* @pkuppens

# Specific ownership for CI/CD and workflows
/.github/ @pkuppens

# Documentation ownership
/docs/ @pkuppens
```

This ensures that @pkuppens is automatically requested for review on all PRs.

### Step 2: Configure Branch Protection via GitHub Web Interface

1. Go to **Settings** → **Branches**
2. Click **Add branch protection rule**
3. Enter `main` as the branch name pattern
4. Configure the settings as outlined above
5. Click **Create** or **Save changes**

### Step 3: Configure Branch Protection via GitHub CLI (Alternative)

```bash
# Requires gh CLI and repository admin permissions
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["setup","lint","test-unit","security","ci-summary"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  --field required_conversation_resolution=true \
  --field restrictions=null
```

## Verification Checklist

After applying branch protection rules:

- [ ] Try to push directly to `main` - should be blocked
- [ ] Create a PR with failing tests - should not be mergeable
- [ ] Create a PR with passing tests - should be mergeable after approval
- [ ] Try to merge with unresolved conversations - should be blocked
- [ ] Verify status checks are required and up-to-date

## Exceptions and Overrides

### When to bypass protection rules

- **Emergency hotfixes**: Critical security vulnerabilities or production-breaking bugs
- **Process**: Requires administrator privileges and should be documented in the PR

### How to handle automation accounts

If you have automation accounts (e.g., Dependabot), add them to the allowlist for specific actions:
- Navigate to **Settings** → **Branches** → **Branch protection rule for main**
- Under **Restrict who can push to matching branches**, add automation account

## Related Documentation

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CI/CD Documentation](./CI_SETUP.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)

## Maintenance

Review and update branch protection rules:
- **Quarterly**: Review required status checks as CI jobs evolve
- **When adding critical jobs**: Update required status checks list
- **When organization policies change**: Align with company-wide requirements

---

**Last Updated**: 2026-02-13  
**Maintained By**: DevOps Team  
**Review Cycle**: Quarterly
