---
name: plan-branch-strategy
description: Ensures work is on a named branch before edits. Use at session start when on main, at planning time before implementation, or when the feature-branch hook blocks edits on main.
---

# Plan branch strategy

## When to use

- **First action in a coding session** (after cloning context): if the repo is on `main`, create a branch before modifying files.
- Start of Phase 2 (plan) per [docs/technical/AGENTS.md](../../../docs/technical/AGENTS.md).
- Any time you notice `git branch --show-current` is `main` and you intend to commit.

## Why

[branch-policy.mdc](../../../.cursor/rules/branch-policy.mdc) and [merge-via-pr](../merge-via-pr/SKILL.md): deliverable work merges to `main` only via pull request. Commits made directly on `main` bypass that workflow.

## Instructions

1. Show current branch: `git branch --show-current`.
2. If the result is **`main`** (or you are in detached HEAD), update and branch:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/NNN-short-slug
   ```
   Use `feature/`, `task/`, `chore/`, or `docs/` per issue type; include the GitHub issue number when there is one (e.g. `feature/128-api-v1-implementation`).
3. If you **already changed files on `main`** but have **not** committed, run only:
   ```bash
   git checkout -b feature/NNN-short-slug
   ```
   Git keeps your working tree; new commits go on the new branch.
4. Verify: `git branch --show-current` is not `main`.

## Naming

See [CLAUDE.md § Git workflow](../../../CLAUDE.md#git-workflow) and [github-integration.mdc](../../../.cursor/rules/github-integration.mdc).

## Integration

- Runs before implementation-heavy skills (e.g. [test](../test/SKILL.md) after code changes).
- Pairs with [merge-via-pr](../merge-via-pr/SKILL.md) for push and PR.

## Note on Cursor skills

This repository gitignores `.cursor/skills` (see [SKILLS_SETUP.md](../../../docs/technical/SKILLS_SETUP.md)). This file is the **committed** copy for Claude Code; keep it in sync with any sibling `plan-branch-strategy` skill in your global Cursor skills pack.
