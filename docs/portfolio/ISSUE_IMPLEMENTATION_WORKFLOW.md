# Issue Implementation Workflow

This workflow ensures issues are validated, planned, and implemented in a consistent way across the portfolio. **AI agents**: read this document before implementing any issue — it defines the required process.

## Principles

| Principle | Practice |
|-----------|----------|
| **Issue review** | Validate before coding — check relevance, existing work, research tooling |
| **Planning** | Architecture review, test strategy, and design before implementation |
| **Feature branching** | All code changes via branches; never commit directly to main for features |
| **Test-driven** | Write tests first where contract is clear; tests drive design |
| **Architecture & design** | Follow SOLID, module boundaries, dependency inversion |

## Prerequisites

- **GitHub CLI (`gh`)**: Authenticate with `gh auth login` so you can fetch and update issues.
- **PowerShell users**: Use `;` instead of `&&` for chained commands (e.g. `git checkout main; git pull`).
- **Quality gate**: `uv sync --group dev` and `uv run pytest` pass before starting.

## Phase 1 — Validate (before writing code)

Verify the issue is still valid and not already done.

### 1.1 Fetch and review the issue

```bash
# From the repo directory
gh issue view <NNN>
```

Check:

- Is the goal still relevant?
- Are acceptance criteria clear and testable?
- Is out-of-scope explicit?

### 1.2 Check if already (partially) implemented

```bash
# Search codebase for relevant symbols or config
rg "<keyword>" --type py
# Or: grep -r "<keyword>" src/
```

- Recent commits touching the area: `git log -p --follow -- <path>`
- PRs that might have closed it: `gh pr list --search "issue" --state merged`

If the work is done or obsolete, update the issue (e.g. `gh issue close NNN --comment "Duplicate of #X"`) and stop.

### 1.3 Research existing tooling and best practices

Before implementing, search for:

- **Libraries**: e.g. "Python justfile alternative", "Makefile vs just vs task"
- **Best practices**: e.g. "py.typed marker PEP 561", "config externalization patterns"
- **Similar solutions**: e.g. "FastAPI project Makefile example"

Use web search or documentation (Context7, docs) to avoid reinventing or picking deprecated approaches.

**Record findings** in the issue (comment) or in `_scratch/` notes if it affects the implementation plan.

---

## Phase 2 — Plan

Create an implementation plan before coding.

### 2.1 Feature branching strategy

**Branch naming** (from [branch-policy.mdc](../../.cursor/rules/branch-policy.mdc)):

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/NNN-short-description` | `feature/79-hybrid-retrieval` |
| Task | `task/NNN-short-description` | `task/80-api-endpoints` |
| Bug | `bug/NNN-short-description` | `bug/42-chunking-edge-case` |
| Hotfix | `hotfix/NNN-short-description` | `hotfix/43-security-patch` |

**Base branch** (from [branch-policy.mdc](../../.cursor/rules/branch-policy.mdc)):

- **Default**: Branch from `main`.
- **Exception**: Branch off a non-main branch when the issue requires tooling (commands, rules, workflows) that exist only on that branch. Example: testing new workflow commands — branch off `feature/workflow-improvements`.

**Branch workflow** (default from main):

```bash
git checkout main
git pull
git checkout -b feature/NNN-short-description
# Or: task/NNN-short-description for smaller tasks
```

**Branch workflow** (when base is non-main):

```bash
git checkout <base-branch>   # e.g. feature/workflow-improvements
git pull
git checkout -b feature/NNN-short-description
```

**Rule**: Feature/task implementation **must** use branches. Direct-to-main is allowed only for docs, config, and agent rules.

### 2.2 Review architecture and design

- Read `CLAUDE.md` (repo and workspace root) for module boundaries
- Check ADRs or `docs/technical/` for relevant decisions
- Identify the correct files and modules to change
- Apply **Architecture principles** (see below)

### 2.3 Architecture and design principles

When implementing, follow:

- **Single responsibility** — each component does one thing; swappable via Strategy/Factory
- **Open/closed** — extend via configuration or new implementation, not by modifying existing code
- **Dependency inversion** — depend on abstractions (Protocol/ABC), inject concretions
- **Interface segregation** — thin API layers: Routes → Services → Repositories → Storage

See [golden-rules.mdc](../../.cursor/rules/golden-rules.mdc) and [AGENTS.md](../technical/AGENTS.md) for details.

### 2.4 Decide test strategy (test-driven)

| Scenario | Approach |
|---------|----------|
| Pure logic, clear contract | **Test-first (TDD)**: write failing test, then implement until it passes |
| API/service integration | Integration test after implementation; mock external services |
| UI / manual flow | Manual check plus existing E2E if any |

Document the test approach in the issue or a brief plan. Run tests after each incremental change.

### 2.5 Assign and optionally comment

```bash
gh issue edit NNN --add-assignee @me
# Optional: gh issue comment NNN --body "Implementation plan: ..."
```

---

## Phase 3 — Implement

Follow the standard Agent Workflow:

1. **Implement in small steps** — one logical change at a time.
2. **Test after each step** — run `uv run pytest` (or subset) frequently.
3. **Quality gate before commit**:
   ```bash
   uv run pytest
   uv run ruff check . && uv run ruff format --check .
   ```
4. **Commit with issue reference**: `#NNN: feat: add py.typed marker`
5. **PR when done**:
   ```bash
   gh pr create --title "#NNN: Add py.typed marker" --body "Closes #NNN"
   ```

---

## gh CLI quick reference

```bash
# View issue
gh issue view 75

# List open issues
gh issue list --state open

# Assign yourself
gh issue edit 75 --add-assignee @me

# Add comment
gh issue comment 75 --body "Implementation plan: ..."

# Create PR (from branch)
gh pr create --title "#75: ..." --body "Closes #75"

# View PR
gh pr view

# Merge PR
gh pr merge --squash --delete-branch
```

---

## Workflow reference (for issue bodies)

When creating or updating issues, include this block so implementers and AI agents know which workflow to follow:

```markdown
## Implementation workflow

Follow [ISSUE_IMPLEMENTATION_WORKFLOW.md](docs/portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md): Validate → Plan → Implement.
- Issue review before coding
- Feature branch from main
- Test-driven where applicable
- Architecture principles (SOLID, dependency injection)
```

## References

- [ISSUES_README.md](./ISSUES_README.md) — Epic structure, verification strategy
- [CLAUDE.md](../../CLAUDE.md) — Repo conventions
- [AGENTS.md](../technical/AGENTS.md) — Agent workflow and testing
- [branch-policy.mdc](../../.cursor/rules/branch-policy.mdc) — When to use branches vs direct-to-main
