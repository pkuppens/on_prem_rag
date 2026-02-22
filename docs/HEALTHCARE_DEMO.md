# Healthcare Clinical Guideline Assistant — Demo Guide

Created: 2026-02-21  
Updated: 2026-02-21

This document describes the healthcare clinical guideline assistant demo (#82): why on-premises matters, how source attribution supports clinical decision-making, and known limitations.

## Why On-Premises Matters for Healthcare

- **Patient data proximity:** Sensitive queries and documents stay on your infrastructure. No patient data or clinical questions are sent to external cloud APIs.
- **Regulatory alignment:** Supports GDPR, NEN 7510 (Dutch healthcare information security), and HIPAA-aware deployments.
- **Auditability:** Every answer includes verifiable source citations (guideline, page). Supports clinical governance and audit trails.

## Source Attribution

The RAG pipeline returns **sources** with every answer. Each source includes:

- **document_name:** The guideline file (e.g. `NHG_Urineweginfecties.pdf`)
- **page_number:** Page in the source document
- **similarity_score:** Retrieval relevance
- **text_preview:** Snippet of the cited passage

**Implementation:** `src/backend/rag_pipeline/core/qa_system.py` — `ask()` returns `sources` derived from retrieved chunk metadata (document_name, page_number).

Clinicians can trace each answer back to the original guideline, section, and page.

## Limitations and Disclaimers

- **Not a substitute for clinical judgment.** The system assists; it does not replace professional decision-making.
- **Guideline currency.** Ingested PDFs are snapshots. Check [richtlijnen.nhg.org](https://richtlijnen.nhg.org) for the latest versions.
- **Language.** Default demo uses Dutch NHG-Standaarden. English guidelines (NICE, WHO) can be added for mixed-language use.
- **Coverage.** Only ingested documents are searchable. Queries outside the corpus receive a low-confidence response.

## Demo Scenario

1. **Fetch guidelines:** `uv run fetch-healthcare-guidelines`
2. **Ingest:** `uv run upload-documents --direct tmp/healthcare_guidelines/*.pdf`
3. **Query example:** "Wat is de eerste keus antibioticum bij cystitis?" → Answer with citation to NHG Urineweginfecties.
4. **Evaluate retrieval:** `uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark_clinical.json`

## Related

- [HEALTHCARE_GUIDELINES_SOURCES.md](portfolio/HEALTHCARE_GUIDELINES_SOURCES.md) — Curated source list and ingestion flow
- Issue #74 — Verification task (run after implementation)
