---
name: get-started
description: Start work on a GitHub issue using the Issue Implementation Workflow (Validate → Plan → Implement). Use when beginning work on an issue, switching issues, or resuming after a session break.
argument-hint: [issue-number or fix issue #N]
---

# Get Started: Issue Workflow

Execute the project's Issue Implementation Workflow for GitHub issue $ARGUMENTS. Parse the issue number from patterns like `fix issue #123`, `issue #45`, `#123`, or `123`. If no number is found, list open issues and ask the user to select one.

## Purpose

Align on the Validate → Plan → Implement process before implementation or planning. Ensures workflow steps are loaded into context.

## Scratch Files and Continuation

Use the project's `tmp/` directory for all scratch files. Enables continuation between sessions.

| File Path | Purpose |
|-----------|---------|
| `tmp/github/issue-descriptions/issue-NNN.md` | Cached issue body from `gh issue view NNN` |
| `tmp/github/progress/issue-NNN-workflow.md` | Workflow state: phase, decisions, validation results, next steps |
| `tmp/github/progress/issue-NNN-plan.md` | Implementation plan (Phase 2 output) |
| `tmp/github/issue-comments/issue-NNN-close.md` | Draft close comment when closing obsolete issues |

**Continuation**: At start, check if `tmp/github/progress/issue-NNN-workflow.md` exists. If it does, read it to load phase and next steps before continuing. Update after each step.

## Writing to GitHub

Significant updates must be written to the GitHub issue so stakeholders see progress. Do not keep them only in tmp/.

| When | What to post | How |
|------|--------------|-----|
| Phase 1: Issue refinement | Refined acceptance criteria, out-of-scope, validation findings | `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-refinement.md` |
| Phase 2: Plan complete | Implementation plan with checklists (tasks, test strategy) | `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-plan.md` |
| Phase 3: Milestones | Completed subtasks, test results | `gh issue comment NNN --body-file ...` when logical milestones are reached |

Draft first in `tmp/github/issue-comments/`, then post when content is ready.

## Prerequisites

- **GitHub CLI (`gh`)**: `gh auth login` if not authenticated
- **PowerShell users**: Use `;` instead of `&&` for chained commands
- **Quality gate**: `uv sync --group dev` and `uv run pytest` pass before starting

## Required Context Loading

**CRITICAL**: Before executing any phase, load:

1. [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md) — full 3-phase workflow
2. [CLAUDE.md](CLAUDE.md) — project conventions, build commands, architecture
3. [.cursor/rules/branch-policy.mdc](.cursor/rules/branch-policy.mdc) — branch naming
4. [.cursor/rules/github-integration.mdc](.cursor/rules/github-integration.mdc) — optional; branch naming, gh CLI

## Execution Workflow

### Step 1: Parse Input

- Extract issue number from $ARGUMENTS (patterns: `#(\d+)`, `issue\s*#?\s*(\d+)`)
- If found → proceed to Step 2
- If not found → go to Step 6 (list open issues, ask user to select)
- **Continuation**: If `tmp/github/progress/issue-NNN-workflow.md` exists, read it first

### Step 2: Load Context

- Read docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md
- Read CLAUDE.md
- **Continuation**: Read tmp/github/progress/issue-NNN-workflow.md if it exists

### Step 3: Fetch Issue

```bash
gh issue view <NNN>
```

- **Write**: Save output to `tmp/github/issue-descriptions/issue-NNN.md`
- **Write**: Create/update `tmp/github/progress/issue-NNN-workflow.md` with issue number, phase, status

**If `gh` fails**: Prompt "Run `gh auth login`" and stop.
**If issue not found**: Report and suggest `gh issue list --state open`.

### Step 4: Phase 1 — Validate

1. **1.1** Check: Goal relevant? Acceptance criteria clear and testable? Out-of-scope explicit?
2. **1.2** Search codebase; check recent commits and merged PRs
3. **1.3** Research tooling and best practices

- **Write**: Update `tmp/github/progress/issue-NNN-workflow.md` with validation results
- **If refinement done**: Draft to `tmp/github/issue-comments/issue-NNN-refinement.md`, then `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-refinement.md`

**If obsolete or already done**:
- Draft close comment to `tmp/github/issue-comments/issue-NNN-close.md`
- Suggest `gh issue close NNN --comment "Duplicate of #X"` or similar
- Stop

**If valid** → proceed to Step 5

### Step 5: Phase 2 — Plan and (Optionally) Implement

- Create branch: `git checkout main; git pull; git checkout -b feature/NNN-short-description` (or task/, bug/, hotfix/)
- Review architecture (CLAUDE.md, docs/technical/)
- Decide test strategy
- Assign: `gh issue edit NNN --add-assignee @me`
- **Write**: Save plan to `tmp/github/progress/issue-NNN-plan.md`
- **Write**: Update `tmp/github/progress/issue-NNN-workflow.md` with phase, branch, plan summary, next steps
- **GitHub**: Draft plan (with checklists) to `tmp/github/issue-comments/issue-NNN-plan.md`, then `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-plan.md`
- If user requested "implement" or "fix": proceed to Phase 3 (small steps, test after each, quality gate before commit)
- If user requested "plan" only: present plan and stop

### Step 6: No Issue Specified

1. Load workflow context (Step 2)
2. Run `gh issue list --state open --limit 20` and display
3. Summarize three-phase workflow
4. **Write** (optional): Save list to `tmp/github/progress/open-issues.md`
5. Ask user to select: `/get-started fix issue #N` or create new issue

## Phase 3 Continuation

During implementation, keep `tmp/github/progress/issue-NNN-workflow.md` updated:
- After each logical step: what was done, tests run, next concrete action
- Next agent reads this file and resumes

## Error Handling

| Condition | Action |
|-----------|--------|
| `gh auth status` fails | Prompt `gh auth login` |
| Issue #NNN not found | Report, suggest `gh issue list --state open` |
| Already on feature branch | Note it; validate and plan; user may want to switch |
| Quality gate fails | `uv sync --group dev` and retry |

## Success Criteria

- Workflow context loaded
- Issue fetched and displayed
- Phase 1 Validate completed (or close if obsolete)
- Phase 2 Plan started (branch created, plan posted to GitHub)
- Scratch files updated for continuation
- Optionally Phase 3 begun

## References

- [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- [CLAUDE.md](CLAUDE.md)
- [tmp/CLAUDE.md](tmp/CLAUDE.md)
