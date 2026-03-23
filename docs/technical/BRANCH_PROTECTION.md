# Branch protection for `main`

Created: 2026-03-23
Updated: 2026-03-23

This repository uses a **branch-first** workflow: contributors merge work through **pull requests** into `main`, not by pushing directly to `main`. GitHub **rulesets** (or classic branch protection) enforce that server-side.

## What to enable

| Rule | Purpose |
|------|---------|
| **Require a pull request before merging** | Blocks direct pushes to `main`; all changes go through a PR. |
| **Require status checks to pass** (optional) | Tie required checks to your CI workflow after they are stable. |
| **Restrict who can push** (optional) | Limit bypass to admins or release role. |

**Suggested for solo/small teams:** require PR with **0** required approvals so you can self-merge after review, while still preventing accidental `git push origin main`.

## Option A — GitHub UI (rulesets)

1. Open **Settings** → **Rules** → **Rulesets** (or **Branches** for classic protection).
2. **New ruleset** → **New branch ruleset**.
3. **Target branches**: add pattern `main` (or `refs/heads/main`).
4. Enable **Require a pull request before merging**.
5. Save and confirm enforcement is **Active**.

## Option B — GitHub CLI + API

A JSON example lives next to this file: [branch-protection-ruleset.example.json](branch-protection-ruleset.example.json).

**Prerequisites:** `gh auth login` with a token that can administer the repository.

```powershell
cd <repo-root>
gh api repos/pkuppens/on_prem_rag/rulesets --method POST --input docs/technical/branch-protection-ruleset.example.json
```

If the call returns `403` or `404`, your token may lack `admin:repo_hook` / admin on the repo — use Option A or ask an owner.

**List rulesets:**

```bash
gh api repos/pkuppens/on_prem_rag/rulesets
```

**Update** an existing ruleset: `PATCH /repos/{owner}/{repo}/rulesets/{ruleset_id}` with a new JSON body.

## Verify

- From a branch, open a small PR — merge should be allowed after checks.
- Try `git push origin main` from a clone — GitHub should **reject** the push (unless you use an admin bypass).

### This repository

A ruleset **Require PR for main** is active (created via API on 2026-03-23). Confirm anytime:

```bash
gh api repos/pkuppens/on_prem_rag/rulesets --jq '.[].name'
```

## References

- [branch-policy.mdc](../../.cursor/rules/branch-policy.mdc)
- [merge-via-pr skill](../../.claude/skills/merge-via-pr/SKILL.md)
- [GitHub: About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
