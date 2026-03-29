# API Redesign (v0 → v1)

Created: 2026-02-23
Updated: 2026-03-29

Ground-up API redesign plan. Treats the current API as v0; designs and implements a new v1. Versioning practice: no long-term parallel support; v0 is removed after v1 migration.

## Scope (Temporary Project Decision)

For this redesign:

- **Client rewrites accepted**: Breaking changes OK; update React frontend, CLI, etc. in lockstep
- **Known clients only**: React frontend, CLI, internal tools. No external/unknown consumers.
- **Revisable**: This is a deliberate, temporary choice. Document for future reference.

## Steps

### Step 1 — Client Needs (by Role)

**Principle**: Use-case driven, not endpoint driven. Legend: **R** = required, **O** = optional, **N** = not used by this client.

#### Capability matrix (client × capability)

| Capability | React app | CLI / scripts | Admin / Ops | Future programmatic |
|------------|-----------|-----------------|-------------|---------------------|
| Document upload (sync, immediate result) | R — upload UI | R — `upload_documents.py` | N | O |
| Document upload (async, task id) | O — can adopt for large files; today uses sync API | O | N | R — reliable bulk |
| List / delete documents | R | R / O | N | R |
| Serve file / extract text (preview) | R | N | N | O |
| Ingest from URL | N | R — automation scripts | N | R |
| Chunk search (retrieval only) | R — `QueryPage` posts to `/api/query` | O — scripts, benchmarks | N | R |
| Medical conversation pipeline | N | O | N | O |
| RAG ask (answer + sources) | R — `QuerySection` | O | N | R |
| Voice RAG | O — voice UX | O — `verify_voice_pipeline.py` | N | N |
| Multi-turn chat / stream | N — no TS caller; primary UI is ask | O | N | O |
| STT (transcribe, draft, info) | R — draft + info; full transcribe as needed | O | N | O |
| Parameter sets | R | O | N | O |
| Health (aggregate + per-service) | R — status UI | O | R — probes, dashboards | O |
| Prometheus metrics | N | N | R | O |
| WebSocket upload progress | R | N | N | N |
| Test / dummy progress | O — dev-only pages | N | N | N |

#### Duplicate upload surfaces (v0)

Today **two** stacks cover uploads: **`/api/documents/*`** (sync) and **`/api/v1/upload`** (async task under `documents_enhanced`). The React app uses **sync** paths from [src/frontend/src/config/api.ts](../../src/frontend/src/config/api.ts). CLI uses sync upload and **from-url**. **v1** merges behaviour under **`/api/v1/documents`** with an explicit **sync vs async** contract (see Step 2).

**Output**: Matrix above + duplicate note.

### Step 2 — Target v1 API Design

- **Version prefix**: `/api/v1/` for application JSON API (except intentionally unversioned ops URLs below).
- **Conventions**: [API_DESIGN.md](API_DESIGN.md), plural nouns, deduplication semantics for uploads (`201` + `created: true` vs `200` + `created: false`) as already captured in rules.
- **Machine-readable draft**: [openapi-v1-draft.yaml](openapi-v1-draft.yaml) — path skeleton and `operationId`s; request/response schemas to be filled in during **#128**.

#### Ops (unversioned; no `/api/v1` prefix)

| Method | Path | Purpose | Notes |
|--------|------|---------|--------|
| GET | `/health` | Liveness | Keep for Docker/Kubernetes probes |
| GET | `/metrics` | Prometheus text | Stable monitoring URL |

#### Documents

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| GET | `/api/v1/documents` | List documents | — | List + metadata | documents |
| POST | `/api/v1/documents` | Create by upload | multipart file, `params_name`; query **`async=true`** for async | Sync: processed payload; async: `task_id` + poll URL | documents |
| DELETE | `/api/v1/documents/{document_id}` | Delete by stable id | — | 204 | documents |
| POST | `/api/v1/documents/ingest-from-url` | Fetch URL and ingest | URL body + params | Same as upload | documents |
| GET | `/api/v1/documents/{document_id}/content` | Raw file or text | `Accept` or `?format=text` | bytes or text | documents |
| GET | `/api/v1/documents/tasks/{task_id}` | Async task status | — | Processing status | documents |
| DELETE | `/api/v1/documents/tasks/{task_id}` | Remove/cancel task-scoped work | — | 204 | documents |

**Decisions**: (1) One document resource collection; async is a mode of `POST`, not a separate top-level `/upload` path. (2) **`document_id`** may be filename or UUID — **#128** picks canonical ids and migration from v0 filenames/task ids. (3) Replaces overlapping **`/api/v1/upload`**, **`/api/v1/list`**, **`/api/v1/status/{task_id}`**, **`/api/v1/task/{task_id}`** with namespaced paths under **`/api/v1/documents/...`**.

#### Retrieval (chunks + conversation)

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| POST | `/api/v1/retrieval/chunks` | Retrieval-only | `query`, strategy, top_k | Chunk list | retrieval |
| POST | `/api/v1/retrieval/conversations` | Medical conversation pipeline | conversation payload | Pipeline result | retrieval |

**Decisions**: Keep **two** operations (chunks vs conversation). Names clarify difference from **QA** below.

#### QA (RAG answers)

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| POST | `/api/v1/qa` | RAG answer | `question`, strategy, `top_k` | Answer + sources | qa |
| POST | `/api/v1/qa/voice` | Audio → RAG | multipart audio | Voice answer | qa |

#### Chat (multi-turn, optional for primary UI)

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| POST | `/api/v1/chat` | Chat completion | messages[] | Chat response | chat |
| POST | `/api/v1/chat/stream` | SSE stream | messages[] + `direct` | text/event-stream | chat |

**Decisions**: **No React dependency today** (see tests: [tests/test_routes.py](../../tests/test_routes.py), [tests/test_chat_stream.py](../../tests/test_chat_stream.py), [scripts/test_chat_stream_local.py](../../scripts/test_chat_stream_local.py)). Keep in v1 for scripts and evaluation; primary product flow remains **ask** and **retrieval**.

#### Speech (STT)

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| POST | `/api/v1/speech/transcribe` | Full STT | audio file | STT response | speech |
| POST | `/api/v1/speech/transcribe/draft` | Draft STT | audio | JSON | speech |
| GET | `/api/v1/speech/info` | Model / capability info | — | JSON | speech |

**Decisions**: Per-router **`/health`** on ask/STT goes away in favour of **unified health** (below).

#### Parameters

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| GET | `/api/v1/parameter-sets` | List parameter sets | — | default + sets[] | parameters |

#### Health (aggregated)

| Method | Path | Purpose | Request (summary) | Response (summary) | Tags |
|--------|------|---------|-------------------|--------------------|------|
| GET | `/api/v1/health` | Rollup status | optional `?deep=true` | JSON | health |
| GET | `/api/v1/health/{component}` | database, llm, vector, auth, websocket | — | JSON | health |

**Decisions**: Replace scattered **`/api/health/*`**, **`/api/ask/health`**, **`/api/stt/health`** with this scheme. **`GET /health`** (root) remains for minimal liveness (ops table).

#### WebSocket

| Path | Purpose | Decision |
|------|---------|----------|
| `/ws/upload-progress` | Upload progress events | **Keep path** in v1 to limit churn; clients already bind via [api.ts](../../src/frontend/src/config/api.ts). Optionally add **`/ws/v1/...`** later as alias. |

#### Test-only

| Method | Path | Purpose | Decision |
|--------|------|---------|----------|
| POST | `/api/v1/test/dummy` | Progress test | Dev/test only; may be disabled in production config in **#128**. |

### Step 3 — Gap Analysis

Map v0 → v1 (or **unchanged** for ops). **Rationale** is short; implementation detail belongs in **#128**.

| v0 Endpoint | v1 Action | Rationale |
|-------------|-----------|-----------|
| GET `/health` | **Unchanged** `GET /health` | K8s/Docker liveness convention |
| GET `/api/health` | `GET /api/v1/health` | Versioned aggregate; optional overlap with root `/health` |
| GET `/api/health/database` | `GET /api/v1/health/database` | Consistent component path |
| GET `/api/health/llm` | `GET /api/v1/health/llm` | Same |
| GET `/api/health/vector` | `GET /api/v1/health/vector` | Same |
| GET `/api/health/auth` | `GET /api/v1/health/auth` | Same |
| GET `/api/health/websocket` | `GET /api/v1/health/websocket` | Same |
| GET `/metrics` | **Unchanged** `GET /metrics` | Prometheus scrape URL stability |
| GET `/api/parameters/sets` | `GET /api/v1/parameter-sets` | Versioned, kebab resource name |
| GET `/api/documents/list` | `GET /api/v1/documents` | REST list collection |
| DELETE `/api/documents/{filename}` | `DELETE /api/v1/documents/{document_id}` | Stable id; **#128** maps filename → id |
| POST `/api/documents/from-url` | `POST /api/v1/documents/ingest-from-url` | Explicit ingest action |
| POST `/api/documents/upload` | `POST /api/v1/documents` (`async=false`) | Unified create document |
| GET `/api/documents/files/{filename}/as-text` | `GET /api/v1/documents/{document_id}/content?format=text` | Sub-resource for content |
| GET `/api/documents/files/{filename}` | `GET /api/v1/documents/{document_id}/content` | Same handler; binary vs text by Accept |
| POST `/api/v1/upload` | `POST /api/v1/documents` (`async=true`) | Merge async upload into documents collection |
| GET `/api/v1/status/{task_id}` | `GET /api/v1/documents/tasks/{task_id}` | Tasks namespaced under documents |
| GET `/api/v1/list` | `GET /api/v1/documents` | Duplicate list removed |
| DELETE `/api/v1/task/{task_id}` | `DELETE /api/v1/documents/tasks/{task_id}` | Align naming with document tasks |
| POST `/api/query` | `POST /api/v1/retrieval/chunks` | Clear retrieval semantics |
| POST `/api/query/process_conversation` | `POST /api/v1/retrieval/conversations` | Group medical pipeline |
| POST `/api/ask` | `POST /api/v1/qa` | Versioned QA resource |
| POST `/api/ask/voice` | `POST /api/v1/qa/voice` | Same |
| GET `/api/ask/health` | `GET /api/v1/health` or component | Drop router-specific health |
| POST `/api/chat` | `POST /api/v1/chat` | Versioned chat |
| POST `/api/chat/stream` | `POST /api/v1/chat/stream` | Versioned streaming |
| WebSocket `/ws/upload-progress` | **Unchanged** (see Step 2) | Avoid unnecessary client churn |
| POST `/api/test/dummy` | `POST /api/v1/test/dummy` | Namespace test routes |
| POST `/api/stt/transcribe` | `POST /api/v1/speech/transcribe` | Group STT under speech |
| POST `/api/stt/transcribe/draft` | `POST /api/v1/speech/transcribe/draft` | Same |
| GET `/api/stt/health` | `GET /api/v1/health` | Unified health |
| GET `/api/stt/info` | `GET /api/v1/speech/info` | Same |

**Naming collision note**: Today **`documents_enhanced`** already uses **`/api/v1`** with **`/upload`**, **`/list`**, etc. The target v1 surface **replaces** those paths with **`/api/v1/documents/...`** so there is a single v1 story. **#128** implements migration and removal of the old partial v1 paths.

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
- [openapi-v1-draft.yaml](openapi-v1-draft.yaml)
- [GitHub #126](https://github.com/pkuppens/on_prem_rag/issues/126)
