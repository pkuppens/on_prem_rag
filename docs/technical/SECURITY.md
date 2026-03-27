# Security Architecture

This document describes the security architecture of the on-premises RAG system, including authentication, access control, privacy protection, audit logging, and regulatory compliance.

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Flow Diagram](#2-data-flow-diagram)
3. [Authentication & Session Management](#3-authentication--session-management)
4. [Access Control (RBAC/ABAC)](#4-access-control-rbacabac)
5. [Privacy Protection & PII Handling](#5-privacy-protection--pii-handling)
6. [Audit Trail](#6-audit-trail)
7. [Guardrails (AI Safety)](#7-guardrails-ai-safety)
8. [Data Deletion & Retention](#8-data-deletion--retention)
9. [Cryptography & Transport Security](#9-cryptography--transport-security)
10. [Compliance Notes](#10-compliance-notes)
11. [Known Limitations & Future Work](#11-known-limitations--future-work)

---

## 1. Architecture Overview

The system is designed for on-premises deployment with **zero cloud dependency** for core operations. All user data, embeddings, and LLM inference stay within the operator's infrastructure by default. Five security-oriented bounded contexts work together:

| Bounded Context   | Responsibility                                          | Code Location                                         |
|-------------------|---------------------------------------------------------|-------------------------------------------------------|
| Identity          | Authentication, OAuth2, JWT session tokens             | `src/backend/auth_service/`                           |
| Access Control    | RBAC/ABAC role enforcement and data-scope isolation    | `src/backend/access_control/`                         |
| Privacy Guard     | PII detection, transformation, cloud-safety rating     | `src/backend/privacy_guard/`                          |
| Audit Trail       | Privacy-preserving event logs for guardrail monitoring | `src/backend/audit_trail/`                            |
| Guardrails        | Input/output safety checks, jailbreak detection        | `src/backend/guardrails/`                             |

Supporting utilities: `src/backend/security/` (JWT helpers, password hashing).

---

## 2. Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          User Browser / Client                              │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ HTTPS (JWT Bearer token)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI RAG Backend                                 │
│                                                                             │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────────────────────┐   │
│  │  Auth Service│    │  Guardrails    │    │   Documents API           │   │
│  │  (JWT/OAuth2)│    │  Manager       │    │   POST /upload            │   │
│  │  port 8001   │    │  ┌──────────┐ │    │   DELETE /{filename}      │   │
│  │              │    │  │ Jailbreak│ │    │   GET  /list              │   │
│  │  /register   │    │  │ Detection│ │    └──────────┬───────────────┘   │
│  │  /login      │    │  ├──────────┤ │               │                   │
│  │  /me         │    │  │ PII      │ │               ▼                   │
│  │  /oauth/...  │    │  │ Check    │ │    ┌──────────────────────┐       │
│  └──────────────┘    │  ├──────────┤ │    │  Document Processing  │       │
│         │            │  │ Access   │ │    │  (chunking, embeddings│       │
│         │JWT Token   │  │ Control  │ │    │   stored locally)     │       │
│         ▼            │  └──────────┘ │    └──────────┬───────────┘       │
│  ┌──────────────┐    └───────┬────────┘               │                   │
│  │ Access       │            │ allow/block             ▼                   │
│  │ Control      │◄───────────┘              ┌──────────────────────┐       │
│  │ (Role +      │                            │   Vector Store        │       │
│  │  DataScope)  │                            │   ChromaDB (local)    │       │
│  └──────┬───────┘                            │   data/chroma/        │       │
│         │                                    └──────────────────────┘       │
│         ▼                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐     │
│  │ Privacy Guard│    │ Audit Trail  │    │   LLM Inference           │     │
│  │ PII detect   │───►│ (hashed IDs, │    │   ┌──────────┐            │     │
│  │ anonymize    │    │  append-only)│    │   │  Local   │ Ollama     │     │
│  └──────────────┘    └──────────────┘    │   │  (on-prem│            │     │
│                                           │   └──────────┘            │     │
│                                           │   ┌──────────┐ optional   │     │
│                                           │   │  Cloud   │ anonymized │     │
│                                           │   │  LLM     │ queries    │     │
│                                           │   └──────────┘ only       │     │
│                                           └──────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────┘

Data at rest:
  data/chroma/      — ChromaDB SQLite files (embeddings + metadata)
  data/database/    — auth.db (hashed passwords, OAuth tokens)
  data/uploads/     — original uploaded files
  data/cache/       — HuggingFace model weights (read-only after download)

All data directories are gitignored and remain on-premises.
```

### Query flow (step by step)

1. **Client** sends request with JWT Bearer token.
2. **Auth Service** (or middleware) validates the token; expired or invalid tokens are rejected (HTTP 401).
3. **Guardrails Manager** evaluates the input:
   - Jailbreak / prompt-injection detection
   - Topic filter (out-of-scope requests blocked)
   - PII detection via Privacy Guard
4. **Access Control** checks role permissions and builds a `DataScope` (patient-scoped queries for the `PATIENT` role).
5. **Privacy Guard** anonymises any PII before the query reaches a cloud LLM; local LLM queries skip anonymisation but PII is still flagged in the audit log.
6. **Audit Trail** records a `GuardrailEventEntry` and (for cloud queries) a `CloudQueryAuditEntry` — both use hashed identifiers, never raw PII.
7. **RAG Pipeline** retrieves relevant chunks from ChromaDB and calls the LLM.
8. **Output Guardrails** validate the LLM response before returning it to the client.

---

## 3. Authentication & Session Management

### Auth microservice (`src/backend/auth_service/`)

| Feature              | Detail                                                                     |
|----------------------|----------------------------------------------------------------------------|
| Protocol             | OAuth 2.0 / OpenID Connect (Google, Microsoft) and local username/password |
| Token type           | JWT (JSON Web Token), signed HS256                                         |
| Access token expiry  | 30 minutes (`ACCESS_TIMEOUT`)                                              |
| Password storage     | bcrypt hash via `passlib.CryptContext`                                     |
| User store           | SQLite (`data/database/auth.db`)                                           |
| Endpoints            | `/register`, `/login`, `/me`, `/logout`, `/oauth/google`, `/oauth/microsoft` |

### JWT utilities (`src/backend/security/security_manager.py`)

- `SecurityManager.create_access_token(data, expires_delta)` — creates a signed JWT with an `exp` claim.
- `SecurityManager.verify_token(token)` — verifies the signature and expiry; returns decoded claims or raises.
- Algorithm: **HS256**; the secret key is injected via environment variable.

### CORS

CORS origins are controlled by the `ALLOW_ORIGINS` environment variable. In development the default is `http://localhost:5173`.

---

## 4. Access Control (RBAC/ABAC)

Implementation: `src/backend/access_control/domain/value_objects.py`

### Roles

| Role      | Description                                      | Can access patient data | Can disable audit |
|-----------|--------------------------------------------------|-------------------------|-------------------|
| `GP`      | General Practitioner — reads/writes records      | Yes (all)               | No                |
| `PATIENT` | Self-service access to own records only          | Own records only        | No                |
| `ADMIN`   | System administration — NO data access           | No                      | No                |
| `AUDITOR` | Compliance review — metadata/logs only (no PII)  | No (metadata only)      | No                |

**Key constraint:** No role can both access data and bypass auditing. The Admin role has zero data permissions by design.

### Permissions

```
READ_OWN_RECORDS      — Patient: own records only
READ_ALL_RECORDS      — GP: all patient records
WRITE_RECORDS         — GP: create/update records
QUERY_LOCAL_LLM       — Query on-premises LLM
QUERY_CLOUD_LLM       — Query cloud LLM (with anonymisation gate)
MANAGE_USERS          — Admin: create/disable accounts
CONFIGURE_SYSTEM      — Admin: settings, parameters
MANAGE_GUARDRAILS     — Admin: guardrail configuration
VIEW_AUDIT_LOGS       — Auditor: read audit log metadata
EXPORT_AUDIT_REPORTS  — Auditor: export compliance reports
```

### Data scope isolation

For the `PATIENT` role, every query automatically receives a `DataScope` filter that restricts ChromaDB results to chunks tagged with that patient's ID. Cross-patient data leakage is monitored by `PatientIsolationAuditEntry`.

---

## 5. Privacy Protection & PII Handling

Implementation: `src/backend/privacy_guard/domain/value_objects.py`

### PII taxonomy

| Category          | Examples (Dutch healthcare)       | Cloud safety          |
|-------------------|-----------------------------------|-----------------------|
| Name              | "Dhr. de Vries"                   | NEVER send to cloud   |
| BSN               | Dutch citizen service number      | NEVER send to cloud   |
| Date of birth     | Exact date                        | NEVER send to cloud   |
| Address           | Street, house number              | NEVER send to cloud   |
| Phone / Email     | Contact details                   | NEVER send to cloud   |
| Patient ID        | Internal record identifier        | NEVER send to cloud   |
| Age (exact)       | "72 jaar" → "70+" after transform | Send after transform  |
| Postal code       | "1234AB" → "123x" region          | Send after transform  |
| Medical terms     | Diagnoses, lab ranges             | Safe as-is            |

### Anonymisation pipeline

1. Detect PII via regex + NLP rules (`PIIType.detection_rules`).
2. Apply transformation tokens (`PIIType.transformation_token`) to replace sensitive values.
3. Output `AnonymizedText` containing:
   - `original_hash` — SHA-256 of the original query (for correlation in audit log, never stored as plaintext).
   - `anonymized_text` — cloud-safe version of the query.
   - `transformations` — list of what was replaced and how.
4. `CloudEligibility` decision: SAFE / AFTER_TRANSFORM / NEVER (blocks cloud LLM call if NEVER).

**Example:** `"Dhr. de Vries, BSN 123456789, 72 jaar"` → `"Mannelijke patiënt, 70+"` (cloud-safe output).

---

## 6. Audit Trail

Implementation: `src/backend/audit_trail/domain/entities.py`

The audit log is **append-only**. No role can delete or modify audit entries.

### Audit entry types

#### `CloudQueryAuditEntry`
Recorded for every query forwarded to a cloud LLM.

| Field                | Stored value                                           |
|----------------------|--------------------------------------------------------|
| `user_role`          | Role enum (not user identity)                          |
| `session_hash`       | Hash of session token (not the token itself)           |
| `original_query_hash`| SHA-256 of original query text                        |
| `anonymized_query`   | Anonymised text sent to cloud                          |
| `pii_categories`     | List of PII types detected                             |
| `cloud_provider`     | Provider name (e.g. "openai")                          |
| `response_status`    | HTTP status from provider                              |
| `latency_ms`         | Round-trip time                                        |

#### `GuardrailEventEntry`
Recorded for every guardrail activation.

| Field            | Stored value                                             |
|------------------|----------------------------------------------------------|
| `guardrail_type` | ACCESS / PII / INTEGRITY / ISOLATION / JAILBREAK         |
| `action`         | ALLOWED / BLOCKED / TRANSFORMED / ESCALATED / WARNING    |
| `query_hash`     | SHA-256 of input query                                   |
| `reason_code`    | Machine-readable reason string                           |
| `confidence`     | Detection confidence score                               |
| `processing_ms`  | Guardrail evaluation time                                |

#### `PatientIsolationAuditEntry`
Recorded when a patient-scoped query is processed. Detects cross-patient data leakage.

| Field              | Stored value                                           |
|--------------------|--------------------------------------------------------|
| `patient_hash`     | Hash of patient ID (not the ID itself)                 |
| `requested_scope`  | Hash of query scope                                    |
| `response_scope`   | Hash of actual data scope returned                     |
| `mismatch_detected`| Boolean — true if scopes differ (potential leak)       |

**Privacy model:** Raw PII is never stored in audit logs. Identifiers are always hashed with a per-deployment salt.

---

## 7. Guardrails (AI Safety)

Implementation: `src/backend/guardrails/`

The Guardrails Manager (`guardrails_manager.py`) orchestrates all checks using NeMo Guardrails (if available) with a custom fallback implementation.

### Input guardrails (`input_guardrails.py`)

| Check               | Description                                              |
|---------------------|----------------------------------------------------------|
| Jailbreak detection | Pattern-based and semantic detection of prompt injections |
| Topic filter        | Blocks out-of-scope requests (non-healthcare topics)     |
| PII detection       | Flags PII; gates cloud LLM usage                         |

### Output guardrails (`output_guardrails.py`)

| Check              | Description                                               |
|--------------------|-----------------------------------------------------------|
| Response safety    | Validates LLM response for harmful or inappropriate content |
| Scope validation   | Ensures response stays within allowed data scope          |

### Guardrail actions (`actions/`)

- `audit_action.py` — writes `GuardrailEventEntry` to audit log.
- `pii_action.py` — triggers anonymisation pipeline.
- `security_action.py` — enforces access-control decisions.

A `GuardrailsResult` object (with `is_allowed` flag and detailed sub-results) is returned for every input/output evaluation.

---

## 8. Data Deletion & Retention

### Delete document endpoint

`DELETE /api/documents/{filename}` (HTTP 204 on success)

Implementation: `src/backend/rag_pipeline/api/documents.py`

**Security controls applied:**
- Path traversal prevention: filenames containing `/`, `\\`, or `..` are rejected with HTTP 400.
- The file must exist on disk; non-existent files return HTTP 404.

**Deletion steps:**
1. Validate filename (no path traversal).
2. Delete all ChromaDB chunks tagged with `document_name == filename` via `VectorStoreManager.delete_by_document_name()`. Returns chunk count deleted.
3. Delete the original file from `data/uploads/`.

**Note:** The deletion endpoint does not currently require authentication. This is a known limitation (see [§11](#11-known-limitations--future-work)).

### Right to erasure (GDPR Article 17)

Deletion of a document removes:
- The original uploaded file from `data/uploads/`.
- All vector embeddings and metadata chunks from ChromaDB.

It does **not** remove audit log entries, which must be retained for compliance. To fully satisfy an erasure request, operators should also purge the auth database user record via the auth service.

### Data retention policy

There is currently no automated data retention or TTL enforcement. Retention is managed operationally:
- **Uploaded files:** Deleted on demand via the API or by removing files from `data/uploads/`.
- **Vector store:** Cleared by calling the delete endpoint or by resetting the ChromaDB directory.
- **Audit logs:** Should be retained for a minimum period required by applicable law (e.g., NEN 7510 recommends 15 years for medical records).
- **Auth database:** User accounts can be deactivated or removed via the admin interface.

---

## 9. Cryptography & Transport Security

| Mechanism             | Algorithm / Library                       | Location                              |
|-----------------------|-------------------------------------------|---------------------------------------|
| JWT signing           | HS256 (HMAC-SHA256)                       | `security/security_manager.py`        |
| Password hashing      | bcrypt (`passlib.CryptContext`)           | `auth_service/main.py`                |
| PII hashing (audit)   | SHA-256 with per-deployment salt          | `audit_trail/domain/entities.py`      |
| Query hash (audit)    | SHA-256                                   | `audit_trail/domain/entities.py`      |
| Transport             | HTTPS (TLS 1.2+) recommended in production| Docker / reverse proxy configuration  |
| Secrets               | Environment variables (never in code)     | `.env` / Docker secrets               |

**Encryption at rest** for the vector store and uploaded files is not enforced at the application layer. Operators should use OS-level or filesystem-level encryption (e.g., LUKS, encrypted volumes) for compliance requirements.

---

## 10. Compliance Notes

### AVG / GDPR (General Data Protection Regulation)

| GDPR Principle            | Implementation status                                                      |
|---------------------------|----------------------------------------------------------------------------|
| Lawful basis              | On-premises deployment; operator is responsible for data processing agreement |
| Data minimisation         | PII anonymisation pipeline; audit logs use hashed identifiers only         |
| Purpose limitation        | Role-based access control limits data access by role                       |
| Accuracy                  | Data stored as uploaded; no automated modification                         |
| Storage limitation        | Manual deletion API available; no automated TTL (known gap)                |
| Integrity & confidentiality| bcrypt passwords, JWT tokens, HTTPS transport recommended                 |
| Right of access (Art. 15) | Data subject can request their data via admin interface                    |
| Right to erasure (Art. 17)| `DELETE /api/documents/{filename}` removes file + embeddings               |
| Data breach notification  | Audit trail provides event log for incident investigation                  |

**DPIA readiness:** The system processes special-category health data (Article 9 GDPR). A Data Protection Impact Assessment (DPIA) is recommended before production deployment. Key topics for the DPIA:
- Lawful basis for processing health data (Article 9(2)(h) for medical purposes)
- Cloud LLM use (only anonymised queries — verify with DPO)
- Patient isolation controls and audit logging

### NEN 7510 (Dutch healthcare information security standard)

NEN 7510 is the Dutch adaptation of ISO/IEC 27001 for healthcare. Relevant controls mapped to this system:

| NEN 7510 Control Area              | System implementation                                          |
|------------------------------------|----------------------------------------------------------------|
| A.9 Access control                 | RBAC with four roles; Patient isolation; append-only audit log |
| A.10 Cryptography                  | bcrypt, HS256 JWT, SHA-256 audit hashing                       |
| A.12 Operations security           | Structured logging; rate limiting middleware                   |
| A.13 Communications security       | HTTPS recommended; CORS controls                               |
| A.14 System acquisition            | On-premises deployment; no vendor lock-in                      |
| A.16 Information security incidents| Audit trail provides event log for incident response           |
| A.18 Compliance                    | This document; DPIA recommended                                |

**Audit log retention:** NEN 7510 and applicable Dutch healthcare law (Wet op de geneeskundige behandelingsovereenkomst, WGBO) require medical records to be retained for a minimum of **20 years**. Audit logs should be retained accordingly. Automated archival is not yet implemented (known gap).

### Suitability statement

This system is designed for on-premises deployment by healthcare operators who bear responsibility as data controllers. The software provides technical safeguards; organisational measures (training, procedures, DPA agreements) remain the operator's responsibility.

---

## 11. Known Limitations & Future Work

| Limitation                                       | Severity | Planned fix                                         |
|--------------------------------------------------|----------|-----------------------------------------------------|
| Delete endpoint has no authentication check      | High     | Add JWT/role guard to `DELETE /api/documents/{filename}` |
| JWT token refresh not implemented                | Medium   | Implement `/token/refresh` endpoint                 |
| JWT token revocation not implemented             | Medium   | Token blocklist (Redis or DB) on logout             |
| No automated data retention / TTL                | Medium   | Background job to expire documents after N days     |
| Encryption at rest not enforced by application   | Medium   | Document operator obligation; optionally add app-layer encryption |
| Audit log storage backend is in-memory/local     | Low      | Persistent append-only store (SQLite or external SIEM) |
| DPIA not yet conducted                           | High (operational) | Conduct DPIA before production deployment with patient data |

---

## References

- [JWT.io](https://jwt.io/) — JWT standard overview
- [GDPR full text](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679)
- [NEN 7510 standard](https://www.nen.nl/nen-7510-2017-nl-235435) — Dutch healthcare IS standard
- [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) — AI safety framework
- [WBSO Architecture](./WBSO_ARCHITECTURE.md) — Detailed privacy-guard and audit-trail design

## Code Files

- [src/backend/security/security_manager.py](../../src/backend/security/security_manager.py) — JWT token creation and verification
- [src/backend/auth_service/main.py](../../src/backend/auth_service/main.py) — Authentication microservice (OAuth2, login, JWT)
- [src/backend/access_control/domain/value_objects.py](../../src/backend/access_control/domain/value_objects.py) — RBAC roles, permissions, data scope
- [src/backend/privacy_guard/domain/value_objects.py](../../src/backend/privacy_guard/domain/value_objects.py) — PII taxonomy, anonymisation
- [src/backend/audit_trail/domain/entities.py](../../src/backend/audit_trail/domain/entities.py) — Audit log entry types
- [src/backend/guardrails/guardrails_manager.py](../../src/backend/guardrails/guardrails_manager.py) — Guardrails orchestrator
- [src/backend/rag_pipeline/api/documents.py](../../src/backend/rag_pipeline/api/documents.py) — Document upload/delete API
