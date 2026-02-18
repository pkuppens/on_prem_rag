# Get Started: Issue Workflow

## Purpose

Start work on a GitHub issue using the project's Issue Implementation Workflow. Ensures workflow steps are loaded into context before implementation or planning. Use this command in new agent chats to align on the Validate → Plan → Implement process.

## Redirect To (do not duplicate)

- **Commits**: Use `/commit` when ready to commit (Phase 3 or after refinement). Do not re-implement commit logic.
- **PR creation**: Use `/pr` when implementation is complete and ready for review.
- **Tests**: Use `/test` or `uv run pytest` for test runs; `/commit` and `/pr` run quality gates when invoked.
- **tmp/ structure**: See [temp-files.mdc](.cursor/rules/temp-files.mdc) for full directory layout and naming. This command uses `tmp/github/` subdirs only.

## When to Use

- New agent chat when working on GitHub issues
- Before implementing any GitHub issue
- When switching to a new issue and you want workflow context loaded
- When you need a quick reminder of the three-phase workflow

## Scratch Files and Continuation

Use the project's `tmp/` directory and its subdirectories for all scratch files during the workflow. This enables continuation between sessions: a new agent can read the workflow state and resume from where the previous session left off.

| File Path | Purpose |
|-----------|---------|
| `tmp/github/issue-descriptions/issue-NNN.md` | Cached issue body from `gh issue view NNN` |
| `tmp/github/progress/issue-NNN-workflow.md` | Workflow state: phase, decisions, validation results, next steps |
| `tmp/github/progress/issue-NNN-plan.md` | Implementation plan (Phase 2 output) |
| `tmp/github/issue-comments/issue-NNN-close.md` | Draft close comment when closing obsolete issues |

**Continuation flow**: At start, check if `tmp/github/progress/issue-NNN-workflow.md` exists. If it does, read it to load phase, decisions, and next steps before continuing. Update this file after each step.

## Writing to GitHub

Significant updates must also be written to the GitHub issue so stakeholders see progress and checklists persist. Do not keep them only in tmp/.

| When | What to post | How |
|------|--------------|-----|
| Phase 1: Issue refinement | Refined acceptance criteria, out-of-scope, validation findings | `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-refinement.md` |
| Phase 2: Plan complete | Implementation plan with checklists (tasks, test strategy) | `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-plan.md` |
| Phase 3: Milestones | Completed subtasks, test results | `gh issue comment NNN --body-file ...` when logical milestones are reached |

- **Draft first** in `tmp/github/issue-comments/` (e.g. `issue-NNN-refinement.md`, `issue-NNN-plan.md`)
- **Post** after user approval or when the content is ready (e.g. completion of refinement or planning)
- **Checklists** in comments stay visible and can be updated by editing the comment (or posting a follow-up)

## Prerequisites

- **GitHub CLI (`gh`)**: Authenticate with `gh auth login` so you can fetch and update issues
- **PowerShell users**: Use `;` instead of `&&` for chained commands (e.g. `git checkout main; git pull`)
- **Quality gate**: `uv sync --group dev` and `uv run pytest` pass before starting any issue

## Command Input

The user may append text after `/get-started`. Parse the issue number and optional base branch from these patterns:

| User Input | Extracted Issue | Base Branch | Example |
|------------|-----------------|-------------|---------|
| `fix issue #123` | 123 | main (default) | `/get-started fix issue #123` |
| `issue #45 branch off feature/X` | 45 | feature/X | `/get-started issue #45 branch off feature/workflow-improvements` |
| `#85 base feature/workflow-improvements` | 85 | feature/workflow-improvements | `/get-started #85 base feature/workflow-improvements` |
| *(empty)* | None | main | `/get-started` |

**Parsing rules**:

- Issue: Match `#(\d+)` or `issue\s*#?\s*(\d+)` — use the first captured number.
- Base branch: Match `branch off\s+(\S+)` or `base\s+(\S+)` — use for branch creation in Step 5. Default: `main`.

If no issue number is found, list open issues (number with title) so the user can select one, or create a new issue.

## Required Context Loading

**CRITICAL**: Before executing any phase, load these files into context:

1. **[docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)** — full 3-phase workflow (Validate, Plan, Implement)
2. **[CLAUDE.md](CLAUDE.md)** — project conventions, build commands, architecture
3. **[.cursor/rules/branch-policy.mdc](.cursor/rules/branch-policy.mdc)** — branch naming and when to use branches
4. **[.cursor/rules/github-integration.mdc](.cursor/rules/github-integration.mdc)** — optional; branch naming, gh CLI reference

## Command Execution Workflow

### Step 1: Parse User Input

- Extract issue number from user text (see Command Input above)
- If found → proceed to Step 2
- If not found → go to Step 6 (show workflow, ask for issue)
- **Continuation**: If `tmp/github/progress/issue-NNN-workflow.md` exists, read it first to resume from last phase

### Step 2: Load Workflow Context

- Read [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- Read [CLAUDE.md](CLAUDE.md)
- Confirm workflow and project conventions are in context
- **Continuation**: If `tmp/github/progress/issue-NNN-workflow.md` exists, read it to load prior phase, decisions, and next steps

### Step 3: Fetch Issue

```bash
gh issue view <NNN>
```

- **Write**: Save output to `tmp/github/issue-descriptions/issue-NNN.md` (cached issue body for reuse)
- **Write**: Create or update `tmp/github/progress/issue-NNN-workflow.md` with: issue number, fetched date, phase (e.g. "Phase 1 Validate"), status

**If `gh` fails** (not authenticated, repo not set):

- Prompt: "Run `gh auth login` to authenticate with GitHub"
- Stop until user authenticates

**If issue not found** (404, invalid number):

- Report: "Issue #NNN not found. Check the number or list issues: `gh issue list --state open`"
- Stop

### Step 4: Phase 1 — Validate (before writing code)

Perform validation as defined in ISSUE_IMPLEMENTATION_WORKFLOW.md:

1. **1.1** Check: Is the goal still relevant? Are acceptance criteria clear and testable? Is out-of-scope explicit?
2. **1.2** Search codebase for relevant symbols; check recent commits and merged PRs
3. **1.3** Research existing tooling and best practices (libraries, patterns, similar solutions)

- **Write**: Update `tmp/github/progress/issue-NNN-workflow.md` with validation results (obsolete/valid, findings, decisions)
- **If refinement done** (e.g. clarified acceptance criteria, added out-of-scope): draft to `tmp/github/issue-comments/issue-NNN-refinement.md`, then post with `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-refinement.md`

**If issue is obsolete or already done**:

- **Write**: Draft close comment to `tmp/github/issue-comments/issue-NNN-close.md`
- Suggest closing: `gh issue close NNN --comment "Duplicate of #X"` or similar
- Stop

**If valid** → proceed to Step 5

### Step 5: Phase 2 — Plan and (Optionally) Implement

- **Base branch**: Use `BASE_BRANCH` if user specified `branch off <branch>` or `base <branch>`; otherwise `main`.
- Create branch: `git checkout BASE_BRANCH; git pull; git checkout -b feature/NNN-short-description` (or `task/`, `bug/`, `hotfix/` per workflow)
- Review architecture (CLAUDE.md, docs/technical/)
- Decide test strategy
- Assign: `gh issue edit NNN --add-assignee @me`
- **Write**: Save implementation plan to `tmp/github/progress/issue-NNN-plan.md`
- **Write**: Update `tmp/github/progress/issue-NNN-workflow.md` with: phase (Phase 2/3), branch name, plan summary, next steps; if BASE_BRANCH ≠ main, add `base_branch: BASE_BRANCH` so `/pr` can target the correct base
- **GitHub**: Draft plan (with checklists) to `tmp/github/issue-comments/issue-NNN-plan.md`, then post with `gh issue comment NNN --body-file tmp/github/issue-comments/issue-NNN-plan.md`
- If user requested "implement" or "fix": proceed to Phase 3 (implement in small steps, test after each, quality gate before commit)
- If user requested "plan" only: present implementation plan and stop

### Step 6: No Issue Specified

When user runs `/get-started` without an issue number:

1. Load workflow context (Step 2)
2. Fetch and display open issues (number with title):

   ```bash
   gh issue list --state open --limit 20
   ```

   The default output shows number and title. Present the list so the user can select an issue.

3. Summarize the three-phase workflow briefly (Phase 1 Validate, Phase 2 Plan, Phase 3 Implement)
4. **Write** (optional): Save list to `tmp/github/progress/open-issues.md` if helpful for session continuity
5. Ask the user to either:
   - **Select an issue**: `/get-started fix issue #N`
   - **Create a new issue**: `gh issue create` (then `/get-started fix issue #N` with the new number)

## Error Handling

| Condition | Action |
|-----------|--------|
| `gh auth status` fails | Prompt user to run `gh auth login` |
| Issue #NNN not found | Report error, suggest `gh issue list --state open` |
| Already on a feature branch | Note it; still validate and plan; user may want to switch |
| Quality gate fails (`uv run pytest`) | Run `uv sync --group dev` and retry; report if still failing |

## Success Criteria

A successful `/get-started fix issue #123` execution results in:

- Workflow context loaded (ISSUE_IMPLEMENTATION_WORKFLOW.md, CLAUDE.md)
- Issue #123 fetched and displayed
- Phase 1 Validate completed (or user directed to close if obsolete)
- Phase 2 Plan started (branch created, architecture reviewed)
- Optionally Phase 3 Implement begun (if user requested fix/implement)
- Scratch files updated in `tmp/github/` so a new session can continue from the current state

## Phase 3 Continuation

During Phase 3 (Implement), keep `tmp/github/progress/issue-NNN-workflow.md` updated:

- After each logical step: what was done, tests run, next concrete action
- If session ends mid-implementation, the next agent reads this file and resumes

## References

- [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- [CLAUDE.md](CLAUDE.md)
- [docs/technical/AGENTS.md](docs/technical/AGENTS.md)
- [tmp/CLAUDE.md](tmp/CLAUDE.md) — scratch directory structure
- [.claude/skills/get-started/SKILL.md](.claude/skills/get-started/SKILL.md) — Claude Code project skill (same workflow, invoke with `/get-started` or `/get-started fix issue #N`)
