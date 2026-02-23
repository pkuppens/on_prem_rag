# Feature Design Guidelines

Created: 2026-02-23
Updated: 2026-02-23

Guidelines for designing new API features. See also [API_DESIGN.md](API_DESIGN.md) for general conventions.

## New Endpoint vs Extend Existing

### Create New Endpoint When

- Different resource or domain action
- Different request/response contract
- Clear separation of concerns
- Extending would complicate the existing contract

### Extend Existing When

- Same resource, minor variant (e.g. `/ask` vs `/ask/voice`)
- Same contract, additive optional parameters
- Avoids endpoint proliferation

### Examples from This Codebase

| Good | Rationale |
|------|------------|
| `/api/ask` + `/api/ask/voice` | Same action (RAG); different input type (text vs audio). Extend. |
| `/api/query` vs `/api/ask` | Different outputs (chunks vs answer). Separate. |
| `/api/documents/upload` vs `/api/documents/from-url` | Different input source; same resource. Could argue either; current: separate. |

### Anti-Pattern

- Multiple endpoints doing the same thing with slight variations (documents vs documents_enhanced) — consolidate in v1

## Checklist for New Endpoints

- [ ] Correct HTTP verb (GET=read, POST=create/action, DELETE=remove)
- [ ] Consistent naming (plural nouns, hierarchical paths)
- [ ] OpenAPI: tags, summary, description, examples
- [ ] Pydantic request/response models
- [ ] Error handling (HTTPException, status codes)
- [ ] Unit tests for route
- [ ] Integration test if calls external service
- [ ] Update [API_ENDPOINTS.md](API_ENDPOINTS.md) and [USAGE.md](../USAGE.md) if user-facing

## References

- [API_DESIGN.md](API_DESIGN.md)
- [API_REDESIGN.md](API_REDESIGN.md)
