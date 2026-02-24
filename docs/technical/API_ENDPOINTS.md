# API Endpoint Inventory

Created: 2026-02-23
Updated: 2026-02-23

This document inventories all API routes in the RAG pipeline. It feeds into [API_REDESIGN.md](API_REDESIGN.md) for the v0 → v1 redesign.

## Full Endpoint List

| Method | Path | Router | Purpose | Response Model |
|--------|------|--------|---------|----------------|
| GET | `/health` | health | Liveness probe | JSON |
| GET | `/api/health` | health | Liveness (API-prefixed) | JSON |
| GET | `/api/health/database` | health | DB connectivity | JSON |
| GET | `/api/health/llm` | health | LLM availability | JSON |
| GET | `/api/health/vector` | health | Vector store status | JSON |
| GET | `/api/health/auth` | health | Auth service status | JSON |
| GET | `/api/health/websocket` | health | WebSocket status | JSON |
| GET | `/metrics` | metrics | Prometheus metrics | text/plain |
| GET | `/api/parameters/sets` | parameters | List parameter sets | JSON |
| GET | `/api/documents/list` | documents | List uploaded files | `{"files": [...]}` |
| DELETE | `/api/documents/{filename}` | documents | Delete document by name | 204 |
| POST | `/api/documents/from-url` | documents | Fetch and process from URL | JSON |
| POST | `/api/documents/upload` | documents | Sync file upload | JSON |
| GET | `/api/documents/files/{filename}/as-text` | documents | Get file content as text | text |
| GET | `/api/documents/files/{filename}` | documents | Get file metadata/content | varies |
| POST | `/api/v1/upload` | documents_enhanced | Async upload (task-based) | UploadResponse |
| GET | `/api/v1/status/{task_id}` | documents_enhanced | Task status | ProcessingStatus |
| GET | `/api/v1/list` | documents_enhanced | List documents (v1) | JSON |
| DELETE | `/api/v1/task/{task_id}` | documents_enhanced | Delete by task ID | 204 |
| POST | `/api/query` | query | Retrieval-only (chunks) | dict (chunks) |
| POST | `/api/query/process_conversation` | query | Medical conversation pipeline | dict |
| POST | `/api/ask` | ask | RAG: question → answer + sources | AskResponse |
| POST | `/api/ask/voice` | ask | Voice input → transcribe → RAG | VoiceAskResponse |
| GET | `/api/ask/health` | ask | Ask endpoint health | JSON |
| POST | `/api/chat` | chat | Chat completion | ChatResponse |
| POST | `/api/chat/stream` | chat | Streaming chat | stream |
| WebSocket | `/ws/upload-progress` | websocket | Upload progress | events |
| POST | `/api/test/dummy` | test | Test progress reporting | JSON |
| POST | `/api/stt/transcribe` | stt | Speech-to-text | STTResponse |
| POST | `/api/stt/transcribe/draft` | stt | Draft transcription | JSON |
| GET | `/api/stt/health` | stt | STT health | JSON |
| GET | `/api/stt/info` | stt | STT info | JSON |

## Overlaps and Gaps

### Documents: v0 vs v1

| v0 (documents) | v1 (documents_enhanced) | Overlap | Notes |
|----------------|-------------------------|---------|-------|
| `POST /api/documents/upload` | `POST /api/v1/upload` | Yes | v1 returns task_id; async. v0 sync. |
| `GET /api/documents/list` | `GET /api/v1/list` | Yes | Similar contract; v1 may differ |
| `DELETE /api/documents/{filename}` | `DELETE /api/v1/task/{task_id}` | Partial | v0 by filename; v1 by task_id |

### Query vs Ask

| Endpoint | Contract | Use Case |
|----------|----------|----------|
| `POST /api/query` | `query` → raw chunks | Retrieval-only; programmatic search |
| `POST /api/ask` | `question` → answer + sources | RAG; user Q&A |

Different semantics: query returns chunks; ask returns LLM answer. Frontend primarily uses `/api/ask` (QuerySection). `/api/query` used for programmatic access to raw retrieval.

### Health Endpoints

- Multiple health routes: `/health`, `/api/health`, and per-service (`/api/health/database`, etc.)
- `ask` and `stt` routers each expose `/health`; paths vary by prefix.

## Known Clients

| Client | Endpoints Used |
|--------|----------------|
| React frontend | `/api/documents/upload`, `/api/documents/list`, `/api/ask`, `/api/chat`, `/ws/upload-progress`, `/api/stt/transcribe` |
| CLI / scripts | `/api/documents/upload`, `/api/documents/from-url`, possibly `/api/ask`, `/api/query` |
| Docker health | `/health` or `/api/health` |
| Metrics (Prometheus) | `/metrics` |

## References

- [API_DESIGN.md](API_DESIGN.md) — Design guidelines
- [API_REDESIGN.md](API_REDESIGN.md) — v0 → v1 redesign plan
