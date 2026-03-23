---
name: merge-via-pr
description: Enforce branch-first delivery. All work merges to main only via pull request from a named branch; never push deliverable commits directly to main. Use for any code, docs, rules, or config change.
---

# Merge via pull request (branch-first)

## When to use

- Starting **any** change that will be committed (code, tests, `docs/`, `.cursor/rules/`, `.claude/skills/`, CI config, `pyproject.toml`, etc.).
- Before `/commit` or `git push` — confirm you are **not** on `main`.

## Core rules

1. **Create a branch first** from updated `main`:

   ```bash
   git checkout main
   git pull origin main
   git checkout -b chore/short-description
   # or: feature/NNN-name, task/NNN-name, docs/short-description
   ```

2. **Commit only on the branch**, then push and open a PR to `main`.

3. **Do not** `git push origin main` for normal work. If you are on `main` by mistake, create a branch before committing: `git checkout -b <type>/<name>` (uncommitted changes move with you).

4. **Stacked PRs**: base branch = parent feature branch when documented in [api-v1-delivery-sequence.md](../../../docs/portfolio/api-v1-delivery-sequence.md).

5. **GitHub issue work**: Implement on `feature/…` or `task/…`; use `Closes #NNN` in the PR body when the issue is done. Update issue checkboxes **when criteria are verified**, then merge via PR ([ISSUE_IMPLEMENTATION_WORKFLOW.md](../../../docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)).

## Exceptions (rare)

- **Repository admins** may use GitHub **bypass** only for emergencies (break-the-glass), not for routine docs.
- **Automated** merges (Dependabot, release bot) follow repository rules; humans still use PRs for hand-written commits.

## Checklist before PR

- [ ] Branch is not `main`
- [ ] `uv run pytest` and ruff gates pass (per project)
- [ ] PR description links issue or explains scope; `Closes #NNN` when applicable

## References

- [branch-policy.mdc](../../../.cursor/rules/branch-policy.mdc)
- [BRANCH_PROTECTION.md](../../../docs/technical/BRANCH_PROTECTION.md)
- [.cursor/commands/commit.md](../../../.cursor/commands/commit.md)
- [.cursor/commands/pr.md](../../../.cursor/commands/pr.md)
