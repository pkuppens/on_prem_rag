# API Redesign (v0 → v1)

Created: 2026-02-23
Updated: 2026-03-23

Ground-up API redesign plan. Treats the current API as v0; designs and implements a new v1. Versioning practice: no long-term parallel support; v0 is removed after v1 migration.

## Scope (Temporary Project Decision)

For this redesign:

- **Client rewrites accepted**: Breaking changes OK; update React frontend, CLI, etc. in lockstep
- **Known clients only**: React frontend, CLI, internal tools. No external/unknown consumers.
- **Revisable**: This is a deliberate, temporary choice. Document for future reference.

## Steps

### Step 1 — Client Needs (by Role)

Identify which functionality each client actually needs:

| Role / Client | Use Cases |
|---------------|-----------|
| Frontend user | Upload docs, list docs, ask questions, chat, voice query, progress feedback |
| CLI user | Upload (file/URL), list, ask (optional) |
| Admin / Ops | Health checks, metrics |
| (Future) Programmatic | Document CRUD, retrieval-only, RAG |

**Output**: Use-case matrix — client × capability. Use-case driven, not endpoint driven.

### Step 2 — Target v1 API Design

Design v1 endpoints that implement only the required functionality:

- Endpoints may be redesigned, combined, deleted, or split
- Apply [API_DESIGN.md](API_DESIGN.md) conventions
- Version prefix: `/api/v1/`

**Candidates** (to be refined):

- Consolidate documents: single upload/list/delete surface (sync + async patterns)
- Clarify query vs ask: keep separate if both needed (retrieval-only vs RAG); otherwise unify
- Unify health: single `/api/v1/health` with sub-resources or query params
- Chat: keep or merge with ask? Depends on client needs

### Step 3 — Gap Analysis

Map v0 → v1:

| v0 Endpoint | v1 Action | Rationale |
|-------------|----------|-----------|
| (to be filled in implementation) | | |

### Step 4 — Implementation Plan

1. Implement v1 endpoints
2. Update clients to use v1
3. Deprecate v0 routes (optional deprecation period)
4. Remove v0 code

**Phased rollout**: Prefer incremental (e.g. documents first, then ask/query) to reduce risk.

## Continuation Issues and Branching Strategy (stacked PRs)

Work is tracked in **#127** → **#128** → **#129** on a **critical path**. Delivery uses **one feature branch per issue** and **stacked pull requests** so each slice is reviewed and merged in order, while keeping history and issue references clear.

### Branch and PR order

| Order | Issue | Branch example (rename to match your naming) | Base branch | Merge first? |
|-------|-------|-----------------------------------------------|-------------|------------|
| 1 | #127 Design | `feature/127-api-v1-design` | `main` | Yes |
| 2 | #128 Implementation | `feature/128-api-v1-implementation` | `main` after #127 merged, **or** branch from `feature/127-*` until #127 merges | After #127 |
| 3 | #129 Load tests | `feature/129-load-test-suite` | `main` after #128 merged, **or** stacked on #128 branch | After #128 |

### Rules

- **Commits**: Reference the issue in messages (e.g. `#127: docs: complete v1 gap table`).
- **Drift**: Regularly merge or rebase `main` into open stacked branches so they do not fall behind.
- **Merge sequence**: Merge the bottom of the stack first (127 PR → then 128 PR → then 129 PR). If using GitHub stacked PRs, set each PR base to the previous feature branch until the parent merges, then retarget to `main`.

### Alternative (not default)

A **single long-lived branch** with one final PR is still possible for a small team; prefer stacked PRs when you want smaller reviews and safer incremental merges.

## Continuation Issues

- **#127**: [TASK] API v1 — Client-needs analysis and target design
- **#128**: [FEAT] API v1 — Implementation and v0 removal (prerequisite: #127)
- **#129**: [TASK] Load test suite

## References

- [API_DESIGN.md](API_DESIGN.md)
- [API_ENDPOINTS.md](API_ENDPOINTS.md)
- [GitHub #126](https://github.com/pkuppens/on_prem_rag/issues/126)
