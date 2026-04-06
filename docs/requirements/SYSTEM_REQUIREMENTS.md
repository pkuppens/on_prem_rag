# System requirements (SR)

**Parent user requirements:** [PRODUCT_REQUIREMENTS_DOCUMENT.md](../PRODUCT_REQUIREMENTS_DOCUMENT.md) (UR-*).  
**Subsystem allocation:** [SOFTWARE_SUBSYSTEM_REQUIREMENTS.md](SOFTWARE_SUBSYSTEM_REQUIREMENTS.md) (SSR-*).  
**Traceability:** [REQUIREMENTS_TRACEABILITY_MATRIX.md](REQUIREMENTS_TRACEABILITY_MATRIX.md).

Created: 2026-04-06  
Updated: 2026-04-06

---

## SR-001 — Document ingestion

The system shall ingest documents from **file upload** and, where supported, from **URLs**, using formats and limits described in product documentation.

**Parents:** UR-001  
**Primary SSR:** SSR-DOC-001, SSR-API-001

## SR-002 — Question answering with sources

The system shall answer user questions using retrieval and generation, and shall return **source references** (e.g. document identifiers, locations, or scores) so users can verify answers.

**Parents:** UR-002  
**Primary SSR:** SSR-QRY-001, SSR-LLM-001

## SR-003 — Retrieval modes

The system shall support **configurable retrieval** for Q&A (including semantic and lexical modes and combined strategies as offered by the product).

**Parents:** UR-002  
**Primary SSR:** SSR-VEC-001, SSR-QRY-002

## SR-004 — HTTP API

The system shall expose a **versioned HTTP API** for ingestion, Q&A, retrieval, health, and related operations documented for integrators.

**Parents:** UR-002, UR-003  
**Primary SSR:** SSR-API-001

## SR-005 — Persistence

The system shall **persist** ingested artefacts and embeddings across restarts in supported deployment models.

**Parents:** UR-001  
**Primary SSR:** SSR-VEC-002, SSR-DEP-001

## SR-006 — Configurable models

The system shall support **configurable** embedding and LLM backends, with a **default on-premises** path documented for operators.

**Parents:** UR-005  
**Primary SSR:** SSR-LLM-002, SSR-VEC-003

## SR-007 — Authentication and sessions

The system shall support **authenticated access** where configured, including a dedicated auth component and documented token/session expectations for production.

**Parents:** UR-006  
**Primary SSR:** SSR-AUTH-001

## SR-008 — Health and readiness

The system shall expose **health or readiness** signals suitable for container orchestration and operations.

**Parents:** UR-006  
**Primary SSR:** SSR-API-002, SSR-DEP-002

## SR-009 — Offline-first and optional external services

The system shall support **offline-first** operation for core ingestion and Q&A. Any **optional external** inference or services shall be **explicitly bounded**, disableable, and documented (no silent dependency on the public internet for core flows).

**Parents:** UR-005  
**Primary SSR:** SSR-LLM-002, SSR-DEP-001

## SR-010 — Web client

The system shall provide a **web client** for upload, query, and related workflows aligned with the API, where the product ships a UI.

**Parents:** UR-002  
**Primary SSR:** SSR-UI-001

## SR-011 — Security posture

The system shall implement **role-based access control**, **audit logging**, and **transport protections** as described in security documentation for production deployments.

**Parents:** UR-006  
**Primary SSR:** SSR-SEC-001, SSR-SEC-002

## SR-012 — Retrieval quality evaluation

The system shall provide a documented means to **evaluate retrieval quality** (e.g. benchmarks or metrics) for representative datasets and strategies.

**Parents:** UR-007  
**Primary SSR:** SSR-EVAL-001

## References

- [USAGE.md](../USAGE.md), [DEPLOYMENT.md](../DEPLOYMENT.md), [API_V1_SPEC.md](../technical/API_V1_SPEC.md), [SECURITY.md](../technical/SECURITY.md)
