# Branch protection for `main`

Created: 2026-03-23
Updated: 2026-04-04

This repository uses a **branch-first** workflow: contributors merge work through **pull requests** into `main`, not by pushing directly to `main`. GitHub **rulesets** (or classic branch protection) enforce that server-side.

## What to enable

| Rule | Purpose |
|------|---------|
| **Require a pull request before merging** | Blocks direct pushes to `main`; all changes go through a PR. |
| **Require linear history** | Merge commits are not allowed on `main`; PRs must use **rebase merge** (or match policy below). |
| **Allowed merge methods: rebase only** | Keeps `main` linear and avoids merge-commit and squash-merge drift. |
| **Block force pushes** (`non_fast_forward`) | Prevents rewriting protected branch history without bypass. |
| **Require status checks to pass** (optional) | Tie required checks to your CI workflow after they are stable. |
| **Restrict who can push** (optional) | Limit bypass to admins or release role. |

**Solo / small teams:** the ruleset uses **0** required approving reviews so you can merge your own PR once checks pass. GitHub still does **not** let the PR author submit an **Approve** review on their own PR in the UI; that is a platform rule, not something the ruleset JSON can change. To record review intent, use a **comment** review, CI green, or an additional reviewer when you have one.

## Repository merge buttons (complement to rulesets)

The ruleset restricts **which merge strategies** apply to `main`. You should also align **repository** settings so the merge dropdown matches:

- **Settings** → **General** → **Pull Requests** → disable **Allow merge commits** and **Allow squash merging**; enable **Allow rebase merging**.

Or via API (owner admin token):

```powershell
gh api repos/pkuppens/on_prem_rag -X PATCH `
  -f allow_merge_commit=false `
  -f allow_squash_merge=false `
  -f allow_rebase_merge=true
```

This was applied for `pkuppens/on_prem_rag` on 2026-03-24 together with the ruleset update.

**Allow auto-merge:** keep **disabled** so dependency and feature PRs merge only after a deliberate action. Full CI still runs on every PR; humans read release notes and merge when ready. Applied for this repo on 2026-04-04:

```powershell
gh api repos/pkuppens/on_prem_rag -X PATCH -f allow_auto_merge=false
```

**Ruleset choice:** keep **`required_approving_review_count`: 0** in [branch-protection-ruleset.example.json](branch-protection-ruleset.example.json) for solo maintainers (merge after green checks without a second approval). Raise to **1** when a second reviewer is available; note GitHub does not let the PR author approve their own PR.

**Organization repos:** if the repo moves under an org, check **Organization → Settings** for any org-wide Dependabot or merge automation that could merge without review.

## Dependabot PRs (human review, no auto-merge)

- Dependabot opens PRs; it does **not** merge from `.github/dependabot.yml`. Merge policy is repository settings + branch rules.
- **Do not** enable auto-merge on individual Dependabot PRs.
- Optional: `assignees` / `reviewers` in `dependabot.yml` notify owners; see [.github/dependabot.yml](../../.github/dependabot.yml).
- **Schedule:** version-update checks run **weekly** on **Sunday 04:00** (`timezone: Europe/Amsterdam` for CET/CEST). `open-pull-requests-limit` limits how many dependency PRs stay open at once so newer runs can replace stale bumps.

## Option A — GitHub UI (rulesets)

1. Open **Settings** → **Rules** → **Rulesets** (or **Branches** for classic protection).
2. **New ruleset** → **New branch ruleset** (or edit **Require PR for main**).
3. **Target branches**: add pattern `main` (or `refs/heads/main`).
4. Enable **Require a pull request before merging**; set **Allowed merge methods** to **Rebase** only.
5. Enable **Require linear history** and **Block force pushes**.
6. Save and confirm enforcement is **Active**.
7. Under **Settings** → **General** → **Pull Requests**, allow **rebase** only (see table above).

## Option B — GitHub CLI + API

A JSON example lives next to this file: [branch-protection-ruleset.example.json](branch-protection-ruleset.example.json).

**Prerequisites:** `gh auth login` with a token that can administer the repository.

**Create** (first time only):

```powershell
cd <repo-root>
gh api repos/pkuppens/on_prem_rag/rulesets --method POST --input docs/technical/branch-protection-ruleset.example.json
```

**Update** an existing ruleset (keep the same `name` and rules; GitHub identifies the ruleset by id):

```powershell
gh api repos/pkuppens/on_prem_rag/rulesets/14226332 --method PUT --input docs/technical/branch-protection-ruleset.example.json
```

If the call returns `403` or `404`, your token may lack `admin:repo_hook` / admin on the repo — use Option A or ask an owner.

**List rulesets:**

```bash
gh api repos/pkuppens/on_prem_rag/rulesets
```

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
