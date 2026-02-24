---
name: api-design
description: Enforce API design rules when adding or changing endpoints. Apply REST conventions, versioning, deduplication semantics, OpenAPI documentation.
---

# API Design Skill

Use when designing new API endpoints, refactoring existing routes, or reviewing API changes. Incorporates lessons from the v0→v1 redesign.

## When to Invoke

- Adding a new route or router
- Changing request/response models
- Refactoring document upload, ask, query, or chat endpoints
- Reviewing API documentation (OpenAPI, /docs, /redoc)
- Deciding between new endpoint vs extending existing

## Core Rules (from API_DESIGN.md)

### 1. HTTP Verbs and Status Codes

| Verb | Use | Idempotent |
|------|-----|------------|
| GET | Retrieve, list, health | Yes |
| POST | Create, action (ask, transcribe) | No (unless designed) |
| PUT | Replace resource | Yes |
| DELETE | Remove | Yes |

**Upload semantics (implemented)**:
- New: 201 Created, `created: true`
- Duplicate (hash match): 200 OK, `created: false` — no file saved, no processing

### 2. Resource Naming

- Plural nouns: `/api/documents`, not `/api/document`
- Hierarchical: `/api/documents/{id}/chunks`
- No verbs in URLs; use HTTP method
- RPC-style actions OK for domain operations: `/api/ask`, `/api/ask/voice`

### 3. New vs Extend

**Create new** when: different resource, different contract, clear separation.
**Extend** when: same resource, minor variant, additive params.

Example: `/api/ask` + `/api/ask/voice` — extend. `/api/query` vs `/api/ask` — separate (chunks vs answer).

### 4. Anti-Patterns (from current codebase)

- **Duplicate endpoints**: `POST /api/documents/upload` and `POST /api/v1/upload` — consolidate in v1.
- **Overlapping semantics**: document list by router — unify contract.
- **Missing OpenAPI metadata**: add tags, summary, description, examples.

### 5. Checklist Before PR

- Correct HTTP verb
- Consistent naming
- OpenAPI tags, description, examples
- Pydantic models for request/response
- Unit tests for route
- API_ENDPOINTS.md updated

## References

- [API_DESIGN.md](../../../docs/technical/API_DESIGN.md)
- [FEATURE_DESIGN_GUIDELINES.md](../../../docs/technical/FEATURE_DESIGN_GUIDELINES.md)
- [API_ENDPOINTS.md](../../../docs/technical/API_ENDPOINTS.md)
- [.cursor/rules/api-design.mdc](../../rules/api-design.mdc)
