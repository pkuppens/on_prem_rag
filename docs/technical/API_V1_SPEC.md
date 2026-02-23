# API v1 Specification

Created: 2026-02-23
Updated: 2026-02-23

Output of Phase 127: client-needs analysis and target v1 API design. Implementation tracked in #128.

## Client Needs (by Role)

| Client / Role | Use Cases | v1 Endpoints |
|---------------|-----------|--------------|
| React frontend | Upload docs, list, ask, chat, voice, progress | POST /api/v1/documents, GET /api/v1/documents, POST /api/v1/ask, POST /api/v1/chat, WS /ws/upload-progress, POST /api/v1/stt/transcribe |
| CLI / scripts | Upload (file/URL), list, ask | Same; from-url under /api/v1/documents |
| Admin / Ops | Health, metrics | GET /api/v1/health, GET /metrics |
| Programmatic | Retrieval-only, RAG | POST /api/v1/query (chunks), POST /api/v1/ask (answer) |

## v1 Design Decisions

### Document Upload

- **Deduplication**: Content-hash check before save and processing. If duplicate: 200 OK, `created: false`. If new: 201 Created, `created: true`.
- **Upload vs processing**: Keep combined for v1 (upload + background process). Separation deferred to future iteration.
- **Sync and async**: v1 supports both sync (`POST /api/v1/documents`) and async task-based (`POST /api/v1/documents/async`) — consolidate documents + documents_enhanced.

### Documents Consolidation

| v0 | v1 | Action |
|----|-----|--------|
| /api/documents/upload | /api/v1/documents | POST, add dedup |
| /api/documents/list | /api/v1/documents | GET |
| /api/documents/{filename} | /api/v1/documents/{filename} | DELETE |
| /api/v1/upload (enhanced) | /api/v1/documents/async | POST, task-based |
| /api/v1/status/{id} | /api/v1/documents/tasks/{id} | GET |
| /api/v1/list | Merge into GET /api/v1/documents | |
| /api/v1/task/{id} | /api/v1/documents/tasks/{id} | DELETE |

### Health Unification

- `GET /api/v1/health` — aggregate; optional `?detail=db,llm,vector,auth,websocket` for sub-checks.

### Query vs Ask

- Keep both: `/api/v1/query` (retrieval-only), `/api/v1/ask` (RAG).

## Gap Analysis (v0 → v1)

| v0 Endpoint | v1 Action | Rationale |
|-------------|-----------|-----------|
| POST /api/documents/upload | POST /api/v1/documents (with dedup) | Add content-hash dedup; 200/201 semantics |
| GET /api/documents/list | GET /api/v1/documents | Rename, unify with v1 list |
| POST /api/v1/upload | POST /api/v1/documents/async | Consistent resource naming |
| Health scattered | GET /api/v1/health | Single entry point |
| /api/ask, /api/query | /api/v1/ask, /api/v1/query | Add v1 prefix |

## Implementation Phases

1. **Phase A**: Add deduplication to existing POST /api/documents/upload (quick win; no client change)
2. **Phase B**: Add /api/v1/* routes alongside v0; migrate frontend config
3. **Phase C**: Remove v0 routes; v0 cleanup

Phase A can ship immediately; B and C in follow-up.
