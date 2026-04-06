# Requirements traceability matrix (RTM)

**Registers:** UR (user), SR (system), SSR (subsystem), VAL (validation).  
**Engineering docs:** [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md), [SOFTWARE_SUBSYSTEM_REQUIREMENTS.md](SOFTWARE_SUBSYSTEM_REQUIREMENTS.md).  
**Portfolio (delivery):** [EPIC-001](../../project/portfolio/epics/EPIC-001.md), [FEAT-001](../../project/program/features/FEAT-001.md)–[FEAT-006](../../project/program/features/FEAT-006.md).

Created: 2026-04-06  
Updated: 2026-04-06

## How to read this matrix

- **VAL-UR-*** — stakeholder / acceptance evidence for a user requirement.  
- **VAL-SR-*** — primary system verification for an SR (tests, CI, manual as listed).  
- **VAL-SSR-*** — verification targeted at a subsystem row (optional; use when SSR needs distinct evidence).  
- **EPIC/FEAT** — cross-reference only; delivery truth stays in `project/`.

## User requirements (UR)

| ID | Statement (summary) | Parent | EPIC / FEAT (typical) | Design / product refs | Validation ID | Evidence (initial) |
|----|---------------------|--------|------------------------|-------------------------|---------------|---------------------|
| UR-001 | Users can ingest documents for Q&A | — | [FEAT-001](../../project/program/features/FEAT-001.md) | [USAGE.md](../USAGE.md), [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md#sr-001--document-ingestion) | VAL-UR-001 | [mvp-end-to-end-flow-verification.md](../portfolio/validation/mvp-end-to-end-flow-verification.md); ingest tests under `tests/` |
| UR-002 | Users get answers with identifiable sources | — | FEAT-001, [FEAT-002](../../project/program/features/FEAT-002.md) | [USAGE.md](../USAGE.md), SR-002 | VAL-UR-002 | MVP flow; API/UI tests |
| UR-003 | Users can run retrieval / search without full generation where offered | — | FEAT-001 | [API_V1_SPEC.md](../technical/API_V1_SPEC.md), SR-004 | VAL-UR-003 | API retrieval scenarios; [INTEGRATION_TESTING.md](../technical/INTEGRATION_TESTING.md) |
| UR-004 | Users can use voice input where STT is enabled (delegates to separate speech product) | — | FEAT-002 | [USAGE.md](../USAGE.md), SR-004 boundary | VAL-UR-004 | MVP flow voice step; STT tests if present |
| UR-005 | Organisation runs core processing on own infrastructure | — | [EPIC-001](../../project/portfolio/epics/EPIC-001.md), FEAT-005 | [DEPLOYMENT.md](../DEPLOYMENT.md), SR-009 | VAL-UR-005 | Deployment docs; compose health |
| UR-006 | Administrators can deploy with auth and health checks | — | FEAT-005, [FEAT-006](../../project/program/features/FEAT-006.md) | [DEPLOYMENT.md](../DEPLOYMENT.md), [SECURITY.md](../technical/SECURITY.md) | VAL-UR-006 | Manual verification playbook; security tests |
| UR-007 | Organisation can measure retrieval quality | — | FEAT-001, FEAT-003 | [RAG_EVALUATION.md](../technical/RAG_EVALUATION.md), SR-012 | VAL-UR-007 | `evaluate-rag` / benchmark docs |

## System requirements (SR)

| ID | Statement (summary) | Parent UR | EPIC / FEAT (typical) | Design refs | Validation ID | Evidence (initial) |
|----|---------------------|-----------|------------------------|-------------|---------------|---------------------|
| SR-001 | Ingestion (upload, URL) | UR-001 | FEAT-001 | [SYSTEM_REQUIREMENTS.md#sr-001--document-ingestion](SYSTEM_REQUIREMENTS.md#sr-001--document-ingestion) | VAL-SR-001 | Pytest ingest; MVP step 1 |
| SR-002 | Q&A with source references | UR-002 | FEAT-001 | SR-002 | VAL-SR-002 | Pytest Q&A; MVP step 2 |
| SR-003 | Configurable retrieval modes | UR-002 | FEAT-001, FEAT-003 | SR-003 | VAL-SR-003 | Retrieval strategy tests; eval CLI |
| SR-004 | Versioned HTTP API | UR-002, UR-003 | FEAT-001 | [API_V1_SPEC.md](../technical/API_V1_SPEC.md) | VAL-SR-004 | Contract/API tests; OpenAPI |
| SR-005 | Persistence of artefacts | UR-001 | FEAT-001, FEAT-005 | [VECTOR_STORE.md](../technical/VECTOR_STORE.md) | VAL-SR-005 | Integration tests; deployment volumes |
| SR-006 | Configurable models | UR-005 | FEAT-003 | [LLM.md](../technical/LLM.md), [EMBEDDING.md](../technical/EMBEDDING.md) | VAL-SR-006 | Config tests; docs |
| SR-007 | Authenticated access | UR-006 | FEAT-002, FEAT-006 | [SECURITY.md](../technical/SECURITY.md) | VAL-SR-007 | Auth service tests |
| SR-008 | Health / readiness | UR-006 | FEAT-005 | [DEPLOYMENT.md](../DEPLOYMENT.md) | VAL-SR-008 | Health endpoint tests |
| SR-009 | Offline-first; optional externals bounded | UR-005 | EPIC-001, FEAT-003 | SR-009 | VAL-SR-009 | NFR review; config docs |
| SR-010 | Web client | UR-002 | FEAT-002 | [FRONTEND_API_CONFIGURATION.md](../FRONTEND_API_CONFIGURATION.md) | VAL-SR-010 | Frontend tests per docs |
| SR-011 | RBAC, audit, transport security | UR-006 | FEAT-006 | [SECURITY.md](../technical/SECURITY.md) | VAL-SR-011 | Security-focused tests |
| SR-012 | Retrieval evaluation tooling | UR-007 | FEAT-001 | [RAG_EVALUATION.md](../technical/RAG_EVALUATION.md) | VAL-SR-012 | Eval CLI; benchmark fixtures |

## Subsystem requirements (SSR) — sample rows

Full list: [SOFTWARE_SUBSYSTEM_REQUIREMENTS.md](SOFTWARE_SUBSYSTEM_REQUIREMENTS.md). Below: one VAL per subsystem row for spot checks; extend as needed.

| ID | Statement (summary) | Parent SR | Validation ID | Evidence (initial) |
|----|---------------------|-----------|---------------|---------------------|
| SSR-DOC-001 | Ingestion pipeline | SR-001 | VAL-SSR-DOC-001 | Loader/chunk tests |
| SSR-VEC-001 | Similarity search | SR-003 | VAL-SSR-VEC-001 | Vector store tests |
| SSR-QRY-001 | Answer assembly | SR-002 | VAL-SSR-QRY-001 | Q&A integration tests |
| SSR-LLM-001 | Generation | SR-002 | VAL-SSR-LLM-001 | LLM provider tests |
| SSR-API-001 | REST surface | SR-004 | VAL-SSR-API-001 | API route tests |
| SSR-UI-001 | Web UI | SR-010 | VAL-SSR-UI-001 | [FRONTEND_TESTS.md](../technical/FRONTEND_TESTS.md) |
| SSR-AUTH-001 | Auth integration | SR-007 | VAL-SSR-AUTH-001 | Auth service tests |
| SSR-SEC-001 | RBAC | SR-011 | VAL-SSR-SEC-001 | Access control tests |
| SSR-EVAL-001 | Benchmarks | SR-012 | VAL-SSR-EVAL-001 | Eval CLI / [RAG_EVALUATION.md](../technical/RAG_EVALUATION.md) |
| SSR-DEP-001 | Container topology | SR-005, SR-009 | VAL-SSR-DEP-001 | [TEST_DOCKER.md](../TEST_DOCKER.md), compose |

## Maintenance

- When you add or change an SR, update this matrix and [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md).  
- When portfolio **FEAT** scope changes, adjust the EPIC/FEAT column (do not rewrite SAFe files from here).  
- Prefer adding evidence links (test path, validation doc) in the **Evidence** column rather than duplicating long prose.
