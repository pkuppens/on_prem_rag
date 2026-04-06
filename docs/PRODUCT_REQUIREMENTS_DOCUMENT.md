# Product Requirements Document: On-Premises RAG Solution

Updated: 2026-04-06

## Overview

The On-Premises RAG Solution allows organisations to use large language models
for document analysis (and, on the roadmap, structured data access) while keeping
controlled data within their infrastructure. The product prioritises **data sovereignty**,
configurable on-premises operation, and compliance-oriented deployments (see [README.md](../README.md),
[TECHNICAL_SUMMARY.md](TECHNICAL_SUMMARY.md)).

## Objectives

- Provide **document ingestion** and **question answering** with **source attribution**
- Deliver interfaces for uploading documents and asking questions (API and web UI)
- Support **multiple LLM and embedding backends** with a documented local-first default
- Offer **natural language to SQL** when document Q&A milestones are stable (program roadmap)
- Provide **enterprise-grade security**, authentication, and deployment tooling

## User requirements (UR)

Engineering detail and traceability: [requirements/README.md](requirements/README.md),
[requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md](requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md).
Portfolio delivery (SAFe) remains in [project/portfolio/epics/](../project/portfolio/epics/) and
[project/program/features/](../project/program/features/).

| ID | Summary |
|----|---------|
| UR-001 | Users can **ingest** documents so the system can answer from their corpus. |
| UR-002 | Users receive **answers with identifiable sources** so they can verify them. |
| UR-003 | Users can use **retrieval / search** without full answer generation where the product offers it. |
| UR-004 | Users can use **voice input** where speech is enabled; core product treats **STT/TTS as a separate reusable product** (boundary, not duplicated here). |
| UR-005 | Organisations run **core processing on their own infrastructure** (on-premises posture). |
| UR-006 | Administrators can **deploy** with containers, **authentication**, and **health checks**. |
| UR-007 | Organisations can **measure retrieval quality** using documented evaluation means. |

**System (SR) and subsystem (SSR) requirements:** [requirements/SYSTEM_REQUIREMENTS.md](requirements/SYSTEM_REQUIREMENTS.md) (**SR-001** through **SR-012**),
[requirements/SOFTWARE_SUBSYSTEM_REQUIREMENTS.md](requirements/SOFTWARE_SUBSYSTEM_REQUIREMENTS.md).

## Key Features (program alignment)

Aligned with [EPIC-001](../project/portfolio/epics/EPIC-001.md) and program features:

1. **Technical foundation & MVP** ([FEAT-001](../project/program/features/FEAT-001.md)) – core document pipeline and Q&A
2. **Enterprise user interface** ([FEAT-002](../project/program/features/FEAT-002.md)) – web UI with upload and chat
3. **Flexible LLM integration** ([FEAT-003](../project/program/features/FEAT-003.md)) – modular provider configuration
4. **Database query capabilities** ([FEAT-004](../project/program/features/FEAT-004.md)) – NL2SQL after document Q&A milestones
5. **Production deployment** ([FEAT-005](../project/program/features/FEAT-005.md)) – containerised infrastructure and operations
6. **Security framework** ([FEAT-006](../project/program/features/FEAT-006.md)) – access control, audit, hardening

## Non-functional requirements

- **Offline-first:** Core ingestion and Q&A shall run **without requiring** the public internet. **Optional** cloud or remote inference **must** be **explicitly configured**, disableable, and documented (see [SYSTEM_REQUIREMENTS.md](requirements/SYSTEM_REQUIREMENTS.md) SR-009).
- **Runtime:** Compatible with **Python 3.12+** (see [README.md](../README.md)) and modern browsers for the shipped UI.
- **Packaging:** Docker (or documented container layout) for repeatable environments ([DEPLOYMENT.md](DEPLOYMENT.md)).
- **Testing:** Automated tests with coverage expectations per [TEST_STRATEGY.md](testing/TEST_STRATEGY.md) and CI; traceability to **VAL-SR-*** in the RTM.
- **Security:** Role-based access control, audit logging, and encrypted transport where deployed ([technical/SECURITY.md](technical/SECURITY.md)).

## Milestones

- **Phase 1:** Document Q&A MVP (Features 001–002)
- **Phase 2:** Flexible LLM and deployment tooling (Features 003, 005)
- **Phase 3:** Security hardening and database queries (Features 004, 006)

## Success metrics

Product and program metrics (response time, adoption, uptime, cost avoidance) remain **targets** for roadmap and portfolio tracking; operationalise in PI planning and demos. Engineering verification uses **VAL-UR-*** and **VAL-SR-*** IDs in [REQUIREMENTS_TRACEABILITY_MATRIX.md](requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md).

## Risks

- **Model performance** – mitigate with benchmarking, evaluation tooling (UR-007 / SR-012), and fallback models
- **Security vulnerabilities** – third-party security review for production; FEAT-006
- **Scalability** – horizontal scaling and load testing as load grows (see [TEST_STRATEGY.md](testing/TEST_STRATEGY.md))

## References

- [README.md](../README.md)
- [requirements/README.md](requirements/README.md) — UR/SR/SSR and RTM index
- [project/SAFe Project Plan.md](../project/SAFe%20Project%20Plan.md)
- [project/portfolio/epics/EPIC-001.md](../project/portfolio/epics/EPIC-001.md)
- [project/program/features/](project/program/features/)

## Code Files

_Intentionally left empty – product requirements; implementation lives under `src/` and is linked from subsystem design docs._
