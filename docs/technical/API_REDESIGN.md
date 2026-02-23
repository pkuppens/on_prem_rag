# API Redesign (v0 → v1)

Created: 2026-02-23
Updated: 2026-02-23

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

## Continuation Issues and Branching Strategy

The implementation is tracked in separate issues (**#127**, **#128**, **#129**) for planning and progress, but delivered from a **single branch**:

- **Branch**: `feature/126-api-architecture-docs` (or `feature/126-api-v1` when implementation starts)
- **Scope**: All work for #126, #127, #128, #129 lands on this branch
- **Phases**: 127 (design) → 128 (impl) → 129 (load tests) are implementation phases, not branch triggers
- **PR**: One PR when complete; merge to main

This keeps the API redesign and documentation as one cohesive deliverable. Sub-issues track phases, not separate branches.

## Continuation Issues

- **#127**: [TASK] API v1 — Client-needs analysis and target design
- **#128**: [FEAT] API v1 — Implementation and v0 removal (prerequisite: #127)
- **#129**: [TASK] Load test suite

## References

- [API_DESIGN.md](API_DESIGN.md)
- [API_ENDPOINTS.md](API_ENDPOINTS.md)
- [GitHub #126](https://github.com/pkuppens/on_prem_rag/issues/126)
