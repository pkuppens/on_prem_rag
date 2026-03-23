# API v1 delivery sequence

Created: 2026-03-23
Updated: 2026-03-23

This document defines **execution order** for the API v0 → v1 redesign so merges and dependencies stay predictable. It complements [ISSUE_IMPLEMENTATION_WORKFLOW.md](./ISSUE_IMPLEMENTATION_WORKFLOW.md) and [API_REDESIGN.md](../technical/API_REDESIGN.md).

## Critical path (fixed order)

| Step | Tracked work | Outcome |
|------|--------------|---------|
| 1 | [Design: client needs, v1 spec, gap analysis](https://github.com/pkuppens/on_prem_rag/issues/127) | Use-case matrix, v1 spec, v0→v1 gap analysis in `docs/technical/` |
| 2 | [Implementation: v1 routes and v0 removal](https://github.com/pkuppens/on_prem_rag/issues/128) | `/api/v1/*` implementation, clients updated, v0 removed |
| 3 | [Load testing suite](https://github.com/pkuppens/on_prem_rag/issues/129) | Load scripts and docs targeting **final** v1 paths |

**Reason:** Load tests must hit stable v1 routes; implementation depends on signed-off design.

Branching: **stacked PRs** per [API_REDESIGN.md § Continuation Issues and Branching Strategy](../technical/API_REDESIGN.md#continuation-issues-and-branching-strategy-stacked-prs).

## Work scheduled around API stability

| Area | When | Note |
|------|------|------|
| [Security and compliance documentation](https://github.com/pkuppens/on_prem_rag/issues/89) | Parallel with late design or after v1 implementation | Prefer documenting **v1** URLs if REST paths are referenced; deletion API tests must match the shipped surface. |
| [RAG evaluation and README metrics](https://github.com/pkuppens/on_prem_rag/issues/133) | After RAG CLI/eval commands and README table contract are stable | Heavy runs may use **manual sign-off**; see [manual-verification-playbook.md](./manual-verification-playbook.md). |

## Quality gate (before each PR)

```text
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

## Traceability

Link acceptance criteria to design and tests using [requirements-design-test-traceability.md](../technical/requirements-design-test-traceability.md).

## References

- [API_REDESIGN.md](../technical/API_REDESIGN.md)
- [manual-verification-playbook.md](./manual-verification-playbook.md)
