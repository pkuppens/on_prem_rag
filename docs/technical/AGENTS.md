# AGENTS.md

## Getting Started

For new agent chats working on GitHub issues: run `/get-started fix issue #N` to load the Issue Implementation Workflow into context and start with Phase 1 (Validate). The command ensures the workflow steps are in context before planning or implementation.

Examples:

- `/get-started fix issue #123` — load workflow and start work on issue 123
- `/get-started` — show workflow summary and ask which issue to work on

## Introduction

This document outlines the workflow for AI coding agents (Claude, Cursor, etc.) when working on this repository. It aligns with the portfolio-wide [Issue Implementation Workflow](../portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md), which defines issue review, planning, feature branching strategies, test-driven development, and architecture principles.

## Prerequisites

- **GitHub CLI (`gh`)**: Use for issue access. Authenticate with `gh auth login` if needed.
- **Quality gate**: `uv sync --group dev` and `uv run pytest` pass before starting any issue.

## Issue Implementation Workflow

### Phase 1 — Validate (before coding)

1. **Fetch and review the issue**
   ```bash
   gh issue view <NNN>
   ```
   Check: Is the goal still valid? Are acceptance criteria clear?

2. **Check if already implemented**
   - Search codebase: `rg <keyword> --type py` or `grep -r <keyword> src/`
   - Recent changes: `git log -p --follow -- <path>`
   - Merged PRs: `gh pr list --search "issue" --state merged`

3. **Research tooling and best practices**
   - Web search for libraries, patterns, and similar solutions
   - Avoid reinventing or choosing deprecated approaches
   - Record findings in the issue or `_scratch/` notes

If the issue is obsolete or done, close it with a comment and stop.

### Phase 2 — Plan

1. **Branch from main**: `git checkout main && git pull && git checkout -b feature/NNN-short-description`
2. **Review architecture**: CLAUDE.md, ADRs, `docs/technical/` for correct module boundaries
3. **Decide test strategy**: Test-first for pure logic; integration for API; manual for UI
4. **Assign yourself**: `gh issue edit NNN --add-assignee @me`

### Phase 3 — Implement

1. Implement in small increments; run `uv run pytest` after each step
2. Quality gate before commit:
   ```bash
   uv run pytest
   uv run ruff check . && uv run ruff format --check .
   ```
3. Commit with issue reference: `#NNN: feat: description`
4. PR when done: `gh pr create --title "#NNN: ..." --body "Closes #NNN"`

**Full workflow:** [ISSUE_IMPLEMENTATION_WORKFLOW.md](../portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)

## Implementation Details

- **Branch Management**: Never commit directly to main. Use feature/task branches and PRs.
- **Commit Strategy**: Multiple commits allowed for separate smaller tasks; reference issue in each.
- **GitHub Actions**: All actions must pass (ruff, pytest). Fix lint issues before pushing.
- **Package Management**: Use `uv add <package>` — never `pip install`.
- **Testing**: All pytest tests must pass. Prefer code coverage for new code.

## Testing Best Practices

### Pytest Guidelines

1. **Assertion Messages** — Include descriptive error messages:
   ```python
   assert pages, "Expected non-empty list of pages"
   ```

2. **Test Documentation** — Each test should have a docstring:
   ```python
   """Test PDF text extraction.
   Verifies that:
   1. The function returns a non-empty list
   2. Each page is a string
   3. The list contains the expected number of pages
   """
   ```

3. **Pytest Features** — Use `pytest.fixture`, `pytest.mark.parametrize`, `pytest.raises()`, `pytest.approx()`.

4. **Type Checking** — Use `isinstance()` checks with descriptive error messages.

### Pre-commit Workflow

After code changes:

```bash
pre-commit run ruff
pre-commit run ruff-format
```

Or: `pre-commit run --all-files`

## gh CLI Quick Reference

```bash
gh issue view 75              # View issue
gh issue edit 75 --add-assignee @me
gh issue comment 75 --body "..."
gh pr create --title "#75: ..." --body "Closes #75"
gh pr merge --squash --delete-branch
```

### Coverage Reports from CI

When reviewing test coverage from a PR or branch run, use `gh run download` to fetch the coverage artifact. The web UI artifacts section may not be visible depending on account/org settings; the CLI always works when authenticated.

```bash
# List recent Python CI runs (get RUN_ID from the first column or from run URL)
gh run list --workflow "Python CI" --limit 5

# Download coverage reports to tmp/coverage-reports
gh run download <RUN_ID> --name coverage-reports --dir tmp/coverage-reports

# Open per-file HTML report (after download)
# tmp/coverage-reports/htmlcov/index.html
```

Artifact contents: `coverage.xml`, `test-results-unit.xml`, `htmlcov/` (per-file report). See [TEST_STRATEGY.md](../testing/TEST_STRATEGY.md) and [CI_SETUP.md](./CI_SETUP.md#coverage-reports) for details.

## References

- [CLAUDE.md](../../CLAUDE.md) — Repo conventions
- [ISSUE_IMPLEMENTATION_WORKFLOW.md](../portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md) — Full 3-phase workflow
- [TESTING_GUIDELINES.md](./TESTING_GUIDELINES.md) — Vector store and embedding test strategy
