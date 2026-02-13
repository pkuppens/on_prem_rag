# Get Started: Issue Workflow

## Purpose

Start work on a GitHub issue using the project's Issue Implementation Workflow. Ensures workflow steps are loaded into context before implementation or planning. Use this command in new agent chats to align on the Validate → Plan → Implement process.

## When to Use

- New agent chat when working on GitHub issues
- Before implementing any GitHub issue
- When switching to a new issue and you want workflow context loaded
- When you need a quick reminder of the three-phase workflow

## Prerequisites

- **GitHub CLI (`gh`)**: Authenticate with `gh auth login` so you can fetch and update issues
- **PowerShell users**: Use `;` instead of `&&` for chained commands (e.g. `git checkout main; git pull`)
- **Quality gate**: `uv sync --group dev` and `uv run pytest` pass before starting any issue

## Command Input

The user may append text after `/get-started`. Parse the issue number from these patterns:

| User Input | Extracted Issue | Example |
|------------|-----------------|---------|
| `fix issue #123` | 123 | `/get-started fix issue #123` |
| `issue #45` | 45 | `/get-started issue #45` |
| `issue 45` | 45 | `/get-started issue 45` |
| `#123` | 123 | `/get-started #123` |
| *(empty)* | None | `/get-started` |

**Parsing rule**: Match `#(\d+)` or `issue\s*#?\s*(\d+)` — use the first captured number.

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

### Step 2: Load Workflow Context

- Read [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- Read [CLAUDE.md](CLAUDE.md)
- Confirm workflow and project conventions are in context

### Step 3: Fetch Issue

```bash
gh issue view <NNN>
```

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

**If issue is obsolete or already done**:

- Suggest closing: `gh issue close NNN --comment "Duplicate of #X"` or similar
- Stop

**If valid** → proceed to Step 5

### Step 5: Phase 2 — Plan and (Optionally) Implement

- Create branch: `git checkout main; git pull; git checkout -b feature/NNN-short-description` (or `task/`, `bug/`, `hotfix/` per workflow)
- Review architecture (CLAUDE.md, docs/technical/)
- Decide test strategy
- Assign: `gh issue edit NNN --add-assignee @me`
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
4. Ask the user to either:
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

## References

- [docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
- [CLAUDE.md](CLAUDE.md)
- [docs/technical/AGENTS.md](docs/technical/AGENTS.md)
