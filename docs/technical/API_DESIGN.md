# API Design Guidelines

Created: 2026-02-23
Updated: 2026-02-23

Production-grade API design guidelines for the on-premises RAG system. Grounded in REST best practices and project decisions.

## REST Conventions

### HTTP Verbs

| Verb | Idempotent | Safe | Use Case |
|------|------------|------|----------|
| GET | Yes | Yes | Retrieve resource(s); no side effects |
| POST | No | No | Create, or actions (e.g. ask, transcribe) |
| PUT | Yes | No | Replace resource |
| PATCH | No | No | Partial update |
| DELETE | Yes | No | Remove resource |

**Current usage**: Most RAG actions use POST (ask, query, upload, transcribe) because they are either creates or non-idempotent operations.

### Resource Naming

- **Plural nouns**: `/api/documents`, `/api/chunks` (not `/document`)
- **Hierarchical paths**: `/api/documents/{id}/chunks`
- **Query params for filtering**: `GET /api/documents?status=processed`
- **Path params for identity**: `GET /api/documents/{filename}`

### Idempotency

- GET, PUT, DELETE should be idempotent
- POST is not idempotent unless explicitly designed (e.g. idempotency keys)
- RAG actions (ask, query) are intentionally non-idempotent

## Endpoint Naming

- Use kebab-case or lowercase in paths
- Avoid verbs in URLs; use HTTP methods (e.g. `POST /api/ask` not `POST /api/askQuestion`)
- Action endpoints (ask, transcribe) are acceptable as RPC-style when they represent domain actions

## OpenAPI, Swagger, ReDoc

### Current Setup

- **FastAPI** auto-generates OpenAPI 3.0 schema at `/openapi.json`
- **Swagger UI**: `/docs` (interactive)
- **ReDoc**: `/redoc` (readable docs)
- **Programmatic clients**: Generate from OpenAPI (e.g. `openapi-generator`, `datamodel-code-generator`)

### Improving Documentation

- Add `tags` to group endpoints
- Add `summary` and `description` to each route
- Add `example` in Pydantic models for request/response samples
- Document error responses (4xx, 5xx)

## Error Handling

### RFC 7807 Problem Details

The app uses RFC 7807-style exception handlers (`exception_handlers.py`):

- `type`: URI identifying the error type
- `title`: Short summary
- `detail`: Human-readable explanation
- `status`: HTTP status code
- `instance`: Request path

### Status Codes

- `400`: Bad request (validation, invalid input)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not found
- `422`: Unprocessable entity (Pydantic validation)
- `500`: Internal server error

## Versioning Strategy

### Current State

- Unversioned routes (e.g. `/api/documents`, `/api/ask`)
- `/api/v1/*` exists for documents_enhanced only

### Versioning Practice (v0 → v1)

- **v0**: Current API (implicit)
- **v1**: Target redesigned API
- **URL versioning**: `/api/v1/documents` preferred for clarity
- **Deprecation**: Document sunset date; remove v0 after migration
- See [API_REDESIGN.md](API_REDESIGN.md)

## REST vs GraphQL

### Decision: REST

**Alternatives considered**:

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| REST | Simple, cacheable, tools (Swagger), stateless | Over-fetching/under-fetching | **Selected** |
| GraphQL | Flexible queries, single endpoint | Complexity, tooling, learning curve | Not selected for current scope |

**Rationale**: On-premises RAG has straightforward CRUD and action patterns. REST fits well. GraphQL would add complexity without clear benefit for current use cases. Re-evaluate if we later need highly variable client query shapes (e.g. many optional nested fields).

## Authentication

- **JWT**: Auth service issues tokens; see `auth_service`
- **OAuth2**: Password and client credentials flows
- **Token lifecycle**: Access + refresh; document expiry policy
- **Protected paths**: Guardrails middleware protects `/api/v1/query`, `/api/v1/analyze`, `/api/v1/chat`

## Horizontal Scaling

- **Stateless design**: No server-side session state; JWT carries identity
- **Session affinity**: Not required if stateless
- **Shared state**: Vector store (ChromaDB), auth tokens — must be external or replicated

## Auditing

- See [.cursor/rules/audit-logging.mdc](../../.cursor/rules/audit-logging.mdc)
- **Do not abbreviate** user inputs in audit logs (questions, prompts)
- **Database audit trail**: Full data in audit tables; log truncation OK if DB holds complete record

## Rate Limiting

- **RateLimitMiddleware**: 120 requests/minute (configurable)
- Prevents abuse; tune per environment

## CORS and Security Headers

- CORS: `ALLOW_ORIGINS` env (comma-separated)
- CSP: Restrict scripts, workers to `self` (see security-best-practices)

## Guidelines for New Features

### New Endpoint vs Extend Existing

| Create New | Extend Existing |
|------------|------------------|
| Different resource or action | Same resource, minor variant |
| Different contract (request/response) | Same contract, additive params |
| Clear separation of concerns | Avoids proliferation |

**Example**: `/api/ask` and `/api/ask/voice` — same action (RAG), different input (text vs audio). Extending is appropriate. `/api/query` vs `/api/ask` — different outputs (chunks vs answer). Separate endpoints.

### Checklist for New Endpoints

- [ ] Correct HTTP verb
- [ ] Consistent naming (plural nouns, hierarchical)
- [ ] OpenAPI tags, description, examples
- [ ] Pydantic request/response models
- [ ] Error handling (HTTPException, RFC 7807)
- [ ] Tests (unit + integration)
- [ ] Documentation in USAGE.md if user-facing

## References

- [API_ENDPOINTS.md](API_ENDPOINTS.md) — Endpoint inventory
- [API_REDESIGN.md](API_REDESIGN.md) — v0 → v1 redesign
- [DOMAIN_DRIVEN_DESIGN.md](DOMAIN_DRIVEN_DESIGN.md) — Bounded contexts
- [.cursor/rules/security-best-practices.mdc](../../.cursor/rules/security-best-practices.mdc)
- [.cursor/rules/audit-logging.mdc](../../.cursor/rules/audit-logging.mdc)
