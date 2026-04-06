# Software / subsystem requirements (SSR)

**Parent system requirements:** [SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md) (SR-*).  
**Traceability:** [REQUIREMENTS_TRACEABILITY_MATRIX.md](REQUIREMENTS_TRACEABILITY_MATRIX.md).

Created: 2026-04-06  
Updated: 2026-04-06

Subsystem prefixes group requirements by bounded area (aligned with [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) and [DOMAIN_DRIVEN_DESIGN.md](../technical/DOMAIN_DRIVEN_DESIGN.md)).

---

## Document processing — SSR-DOC-*

### SSR-DOC-001 — Ingestion pipeline

The **ingestion** path shall accept supported file types and URL ingestion where offered, normalize content for chunking, and emit progress or status suitable for API/UI consumers.

**Parents:** SR-001  
**Design:** [PDF_PROCESSING.md](../technical/PDF_PROCESSING.md), [CHUNKING.md](../technical/CHUNKING.md)

---

## Vector store — SSR-VEC-*

### SSR-VEC-001 — Similarity search

The **vector store** shall support similarity search for chunks used in Q&A and retrieval-only flows.

**Parents:** SR-003  
**Design:** [VECTOR_STORE.md](../technical/VECTOR_STORE.md), [CHROMADB_SCHEMA.md](../technical/CHROMADB_SCHEMA.md)

### SSR-VEC-002 — Durable storage

The **vector store** shall use persisted storage paths in documented deployments so embeddings survive restarts.

**Parents:** SR-005  
**Design:** [VECTOR_STORE.md](../technical/VECTOR_STORE.md), [DEPLOYMENT.md](../DEPLOYMENT.md)

### SSR-VEC-003 — Embedding configuration

The **embedding** layer shall be selectable via configuration documented for operators.

**Parents:** SR-006  
**Design:** [EMBEDDING.md](../technical/EMBEDDING.md)

---

## Query and orchestration — SSR-QRY-*

### SSR-QRY-001 — Answer assembly

The **query** orchestration shall combine retrieved chunks with the configured LLM and return answers including **source metadata**.

**Parents:** SR-002  
**Design:** [DOMAIN_DRIVEN_DESIGN.md](../technical/DOMAIN_DRIVEN_DESIGN.md), [TOP_K_RETRIEVAL.md](../technical/TOP_K_RETRIEVAL.md)

### SSR-QRY-002 — Hybrid / lexical retrieval

Where the product offers lexical or hybrid retrieval, the **query** layer shall combine or select retrieval modes per configuration.

**Parents:** SR-003  
**Design:** [RAG_EVALUATION.md](../technical/RAG_EVALUATION.md)

---

## LLM provider — SSR-LLM-*

### SSR-LLM-001 — Generation

The **LLM** integration shall generate answers conditioned on retrieved context within documented limits.

**Parents:** SR-002  
**Design:** [LLM.md](../technical/LLM.md)

### SSR-LLM-002 — Backend selection

The **LLM** integration shall support multiple backends via configuration, including local inference; optional cloud backends remain explicit and disableable.

**Parents:** SR-006, SR-009  
**Design:** [LLM.md](../technical/LLM.md)

---

## API host — SSR-API-*

### SSR-API-001 — REST surface

The **API** layer shall implement documented REST endpoints for documents, Q&A, retrieval, and related resources under the versioned API.

**Parents:** SR-001, SR-002, SR-004  
**Design:** [API_V1_SPEC.md](../technical/API_V1_SPEC.md)

### SSR-API-002 — Health endpoints

The **API** layer shall expose health/readiness endpoints suitable for deployment checks.

**Parents:** SR-008  
**Design:** [DEPLOYMENT.md](../DEPLOYMENT.md), [API_ENDPOINTS.md](../technical/API_ENDPOINTS.md)

---

## Web UI — SSR-UI-*

### SSR-UI-001 — Primary web experience

The **frontend** shall provide flows for upload, query, and viewing responses consistent with the API (for product builds that include the React UI).

**Parents:** SR-010  
**Design:** [FRONTEND_API_CONFIGURATION.md](../FRONTEND_API_CONFIGURATION.md)

---

## Auth — SSR-AUTH-*

### SSR-AUTH-001 — Auth service integration

The **auth** subsystem shall integrate with the documented auth microservice (tokens, OAuth where configured) for protected deployments.

**Parents:** SR-007  
**Design:** [SECURITY.md](../technical/SECURITY.md), [DEPLOYMENT.md](../DEPLOYMENT.md)

---

## Security cross-cutting — SSR-SEC-*

### SSR-SEC-001 — RBAC

The system shall enforce **role-based access** per documented models where enabled.

**Parents:** SR-011  
**Design:** [SECURITY.md](../technical/SECURITY.md)

### SSR-SEC-002 — Audit trail

The system shall record **audit** events for security-sensitive actions per documentation.

**Parents:** SR-011  
**Design:** [SECURITY.md](../technical/SECURITY.md)

---

## Evaluation — SSR-EVAL-*

### SSR-EVAL-001 — Benchmarks

The **evaluation** tooling shall run documented benchmarks and report metrics for configured datasets and retrieval strategies.

**Parents:** SR-012  
**Design:** [RAG_EVALUATION.md](../technical/RAG_EVALUATION.md)

---

## Deployment — SSR-DEP-*

### SSR-DEP-001 — Container topology

**Deployment** artefacts shall document compose or container layout, ports, volumes, and persistence expectations.

**Parents:** SR-005, SR-008, SR-009  
**Design:** [DEPLOYMENT.md](../DEPLOYMENT.md), [PORTS.md](../PORTS.md)

### SSR-DEP-002 — Operations signals

**Deployment** documentation shall describe how operators use health endpoints and logs for core services.

**Parents:** SR-008  
**Design:** [DEPLOYMENT.md](../DEPLOYMENT.md)

---

## Boundary: speech product (not core SSR detail)

Core RAG may expose **voice input** that delegates to a **separate STT/TTS product** for reuse across projects. Detailed STT/TTS subsystem requirements are **out of scope** for this file; link from RTM as a boundary only (see [README.md](README.md)).

**Parents:** SR-004 (when voice is in scope for the deployment)  
**Note:** Map to **VAL-SR-004** at system level; do not duplicate a full SSR list for STT here.
