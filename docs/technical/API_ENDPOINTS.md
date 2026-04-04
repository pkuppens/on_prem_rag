# API Endpoint Inventory

Created: 2026-02-23
Updated: 2026-04-05

This document inventories the **versioned** RAG API under `/api/v1`. Unversioned ops endpoints stay at the paths below. Historical v0 routes were removed in issue #128; see [API_REDESIGN.md](API_REDESIGN.md) for the v0 → v1 map.

## Full Endpoint List

| Method | Path | Router | Purpose | Response |
|--------|------|--------|---------|----------|
| GET | `/health` | health | Root liveness (ops) | JSON |
| GET | `/metrics` | metrics | Prometheus metrics | text/plain |
| GET | `/api/v1/documents` | documents | List uploaded files | `{"files": [...]}` |
| POST | `/api/v1/documents` | documents | Sync upload (`multipart` field `file`) or async (`?async=true`, field `files`) | JSON / `UploadResponse` |
| POST | `/api/v1/documents/ingest-from-url` | documents | Fetch and process from URL | JSON |
| DELETE | `/api/v1/documents/{document_id}` | documents | Delete document (filename id) and vectors | 204 |
| GET | `/api/v1/documents/{document_id}/content` | documents | File bytes or `?format=text` | file / text |
| GET | `/api/v1/documents/tasks/{task_id}` | documents | Async task status | `ProcessingStatus` |
| DELETE | `/api/v1/documents/tasks/{task_id}` | documents | Cleanup completed task workspace | 204 |
| POST | `/api/v1/retrieval/chunks` | query | Retrieval-only (chunks) | dict |
| POST | `/api/v1/retrieval/conversations` | query | Medical conversation pipeline | dict |
| POST | `/api/v1/qa` | ask | RAG: question → answer + sources | `AskResponse` |
| POST | `/api/v1/qa/voice` | ask | Voice input → transcribe → RAG | `VoiceAskResponse` |
| POST | `/api/v1/chat` | chat | Chat completion | `ChatResponse` |
| POST | `/api/v1/chat/stream` | chat | Streaming chat (SSE) | stream |
| WebSocket | `/ws/upload-progress` | websocket | Upload progress | events |
| POST | `/api/v1/test/dummy` | test | Test progress reporting | JSON |
| POST | `/api/v1/speech/transcribe` | stt | Speech-to-text | `STTResponse` |
| POST | `/api/v1/speech/transcribe/draft` | stt | Draft transcription | JSON |
| GET | `/api/v1/speech/info` | stt | STT capability info | JSON |
| GET | `/api/v1/parameter-sets` | parameters | List RAG parameter sets | JSON |
| GET | `/api/v1/health` | health | Aggregate health (optional `deep=true`) | JSON |
| GET | `/api/v1/health/{component}` | health | Per-component health (`database`, `llm`, `vector`, `auth`, `websocket`) | JSON |

## Retrieval vs QA

| Endpoint | Contract | Use case |
|----------|----------|----------|
| `POST /api/v1/retrieval/chunks` | `query` → raw chunks | Retrieval-only; programmatic search |
| `POST /api/v1/qa` | `question` → answer + sources | RAG; user Q&A |

Different semantics: retrieval returns chunks; QA returns an LLM answer. The React Query UI uses retrieval for search and QA/voice where configured; see [src/frontend/src/config/api.ts](../../src/frontend/src/config/api.ts).

## Health

- **Root** `GET /health` — minimal liveness for load balancers and Docker.
- **Versioned** `GET /api/v1/health` and `GET /api/v1/health/{component}` — richer checks. Per-router `/health` endpoints under `/api/ask` or `/api/stt` were removed.

## Known Clients

| Client | Endpoints used |
|--------|----------------|
| React frontend | `/api/v1/documents`, `/api/v1/retrieval/chunks`, `/api/v1/qa`, `/api/v1/qa/voice`, `/api/v1/speech/*`, `/api/v1/parameter-sets`, `/api/v1/health`, `/ws/upload-progress` ([api.ts](../../src/frontend/src/config/api.ts)) |
| CLI / scripts | `/api/v1/documents`, `/api/v1/documents/ingest-from-url`, `/api/v1/qa`, `/api/v1/retrieval/chunks` |
| Docker health | `/health` |
| Metrics (Prometheus) | `/metrics` |

## References

- [API_DESIGN.md](API_DESIGN.md) — Design guidelines
- [API_REDESIGN.md](API_REDESIGN.md) — v0 → v1 redesign plan
- [openapi-v1-draft.yaml](openapi-v1-draft.yaml) — Draft OpenAPI for `/api/v1`
