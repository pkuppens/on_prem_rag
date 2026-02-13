# Portfolio GitHub Issues

Issues for the on-premises RAG MVP are tracked on GitHub.

## Issue Implementation Workflow

Before working on an issue, follow the **[Issue Implementation Workflow](./ISSUE_IMPLEMENTATION_WORKFLOW.md)**:

1. **Validate** — Issue review before coding: `gh issue view NNN`, check if already done, research tooling
2. **Plan** — Architecture review, feature branching strategy, test-driven approach, design principles
3. **Implement** — Small increments, quality gate, commit with `#NNN: type: desc`

**AI agents**: Read `ISSUE_IMPLEMENTATION_WORKFLOW.md` before implementing any issue. It defines issue review, planning, feature branching, test-driven development, and architecture principles.

## Epic and Linked Issues

**[Epic #91](https://github.com/pkuppens/on_prem_rag/issues/91): On-Premises RAG MVP — Job-Ready Portfolio**

The Epic links to all work and verification issues. View at: https://github.com/pkuppens/on_prem_rag/issues

## Verification Strategy

Verifications ensure the project meets MVP and technical quality before portfolio/demo use. Each verification issue contains full, self-contained instructions.

| Verification | Issue | Type   | Scope      |
|--------------|-------|--------|------------|
| Technical state | #72 | Both   | ruff, pytest, architecture |
| MVP flow     | #73 | Human  | upload → query → voice    |
| Healthcare   | #74 | Human  | clinical guideline assistant |

### Automated checks (#72)

```bash
uv sync --group dev
uv run ruff check . && uv run ruff format --check .
uv run pytest
pre-commit run --all-files
```

### Human checks

Each verification issue includes step-by-step instructions. Follow them in order and check off the acceptance criteria in the issue.

## Issue Templates

Templates in `.github/ISSUE_TEMPLATE/`:

| Template      | Use case                                      |
|---------------|-----------------------------------------------|
| verification  | MVP or technical validation (automated/human/both) |
| feature       | Key capability (includes effort, out-of-scope) |
| epic          | High-level initiative                          |
| story, task, demo, cicd, test | As per SAFe / project conventions |

## References

- [ISSUE_IMPLEMENTATION_WORKFLOW.md](./ISSUE_IMPLEMENTATION_WORKFLOW.md) — Validate → Plan → Implement
- [CLAUDE.md](../../CLAUDE.md) — repo conventions
- [AGENTS.md](../technical/AGENTS.md) — agent workflow and gh CLI
