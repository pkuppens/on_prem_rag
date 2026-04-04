# Security architecture

**Updated:** 2026-04-05

This document describes **security-related components** that exist in the repository today. For vulnerability reporting, see the root [SECURITY.md](../../SECURITY.md). For **data flows** and **GDPR / NEN 7510 / DPIA** readiness notes, see [SECURITY_DATA_FLOW_AND_COMPLIANCE.md](SECURITY_DATA_FLOW_AND_COMPLIANCE.md). Authentication flows are detailed in [AUTHENTICATION_AUTORISATION.md](../AUTHENTICATION_AUTORISATION.md).

## Goals

- **On-premises first:** Keep sensitive documents and embeddings under the operator’s control when deployed accordingly.
- **Defense in depth:** Authentication, authorization, auditability, PII awareness, and LLM guardrails are separate concerns with dedicated modules.
- **Documented behaviour:** Prefer linking to code and technical docs over marketing claims.

## Component map

| Area | Role | Code location |
| ---- | ---- | ------------- |
| JWT helpers | Token creation and verification utilities | [src/backend/security/security_manager.py](../../src/backend/security/security_manager.py) |
| Auth microservice | OAuth2-oriented flows, sessions, user store (SQLite) | [src/backend/auth_service/](../../src/backend/auth_service/) |
| Access control | Role and permission model (domain-driven) | [src/backend/access_control/](../../src/backend/access_control/) |
| Audit trail | Audit entities and logging related to guardrails and access | [src/backend/audit_trail/](../../src/backend/audit_trail/) |
| Privacy guard | PII-oriented checks and utilities | [src/backend/privacy_guard/](../../src/backend/privacy_guard/) |
| NeMo Guardrails | Input/output rails, config, integration hooks | [src/backend/guardrails/](../../src/backend/guardrails/) |
| RAG API | Document upload, listing, **delete** (file + vectors), chat | [src/backend/rag_pipeline/api/](../../src/backend/rag_pipeline/api/) |

## Authentication and authorization

- The **auth_service** exposes registration, login, session validation, and OAuth-related endpoints (see [AUTHENTICATION_AUTORISATION.md](../AUTHENTICATION_AUTORISATION.md)).
- **JWT** usage for services that rely on bearer tokens is supported via `security_manager` and related helpers.
- **access_control** encodes role-based rules in code (see domain and value objects). Integrations with the FastAPI layer depend on how routes enforce permissions; treat route-level auth as part of your deployment review.

## Audit and guardrails

- **audit_trail** defines audit log types and entities used when guardrails and monitoring record events.
- **guardrails** loads NeMo-style configuration (`config.yml`, `rails.co`), exposes a guardrails manager, and applies input/output actions (including PII-related actions and security actions). Chainlit and other frontends may wire guardrails through callbacks (for example [src/frontend/chat/handlers/agent_callbacks.py](../../src/frontend/chat/handlers/agent_callbacks.py)).

## Data lifecycle and erasure

- Uploaded documents live in the configured upload directory.
- Chunks and embeddings are stored in the configured vector store (default: ChromaDB via the vector store manager).
- **Deletion:** `DELETE /api/v1/documents/{document_id}` removes the file and associated chunks in the vector store ([documents.py](../../src/backend/rag_pipeline/api/documents.py); `document_id` is the stored filename today). This supports **data minimisation** and **erasure** workflows but does not replace backup rotation or log redaction policies.

## Related documentation

- [VECTOR_STORE.md](VECTOR_STORE.md) — storage behaviour
- [LLM.md](LLM.md) — inference backends
- [CHROMADB_SCHEMA.md](CHROMADB_SCHEMA.md) — metadata fields

## References

- [JWT](https://jwt.io/)

## Code Files

- [src/backend/security/security_manager.py](../../src/backend/security/security_manager.py) — JWT token creation and verification helper
- [src/backend/auth_service/](../../src/backend/auth_service/) — Authentication microservice
- [src/backend/access_control/](../../src/backend/access_control/) — Role-based access control domain
- [src/backend/audit_trail/](../../src/backend/audit_trail/) — Audit logging entities and services
- [src/backend/privacy_guard/](../../src/backend/privacy_guard/) — PII and privacy utilities
- [src/backend/guardrails/](../../src/backend/guardrails/) — NeMo Guardrails configuration and manager
- [src/backend/rag_pipeline/api/documents.py](../../src/backend/rag_pipeline/api/documents.py) — Document CRUD including delete with vector purge
- [tests/test_routes.py](../../tests/test_routes.py) — API tests including document delete
