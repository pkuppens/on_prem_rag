# Test Strategy

Created: 2025-02-20  
Updated: 2025-02-20

## Overview

This document defines the testing strategy for the on-premises RAG project: test pyramid policy, marker usage, and deduplication guidelines. It supports issue #118 (testing strategy redesign).

## Test Pyramid Policy

### Layers

| Layer | Purpose | Example | Markers |
|-------|---------|---------|---------|
| **Unit** | Test logic in isolation; fast; no external services | `chunk_documents()`, `DocumentLoader.load_document()` with small files | Default (no slow/internet) |
| **Integration** | Test wiring between components; may use real models/network | PDF → chunk → embed → store pipeline | `slow`, `internet` |
| **E2E** | Full stack; Docker, real services | Backend + auth + frontend | `docker` |

### Rule: No Duplicate Assertions

- **Unit tests** cover business logic (e.g. chunking algorithm, duplicate detection logic).
- **Integration tests** cover wiring (e.g. pipeline from PDF to vector store).
- **Never** assert the same behavior in both: if a unit test validates `chunk_documents` output, integration tests should not re-assert that same contract—they assert end-to-end results.

### Rule: Unit Tests Use Light Data

- Prefer synthetic or small fixture data for unit tests.
- Avoid loading full 144-page PDFs in unit tests; use smaller files or mocks.
- If a test needs a real PDF, use the smallest available (e.g. 2005.11401v4.pdf) and consider `@pytest.mark.slow`.

## Marker Policy

### Execution Context

- **Default**: Unit tests (no marker). Run in CI fast path.
- **slow**: >5s or model loading. Run in performance job.
- **internet**: Requires network. Run in integration job.
- **ollama**, **docker**, **cloud_llm**: Specialized resources. Run manually or in dedicated jobs.

### CI Behaviour

- **guardrails_ci_skip**: PyTorch CPU compatibility on some GitHub runners.
- **ci_skip**: Missing models or runner resources.
- **ci_setup**: CI configuration validation.

### New Test Requirement

Every new test must have at least one category marker (`unit` implied by default, or `slow`, `internet`, etc.) so CI can select the right subset.

## Deduplication Audit (2025-02-20)

### Findings

1. **DocumentLoader (duplicate coverage)**  
   - `tests/core/test_document_loader.py`: Unit tests with small text/md/html files; `test_duplicate_detection` uses a temp text file.  
   - `tests/test_document_loader.py`: PDF-focused tests; `test_duplicate_detection` and `test_metadata_consistency` use the full 144-page PDF (2303.18223v16.pdf), causing ~6s each.  
   - **Recommendation**: Use smaller PDF (2005.11401v4.pdf) for duplicate/consistency tests in `test_document_loader.py`, or move PDF-heavy tests to integration. Reduces unit job time without losing coverage.

2. **Chunking vs integration**  
   - `tests/test_chunking.py`: Pure `chunk_documents()` with `Document` objects.  
   - `tests/test_pdf_embedding_integration.py`: Full pipeline; chunking exercised via `chunk_pdf()`.  
   - **Status**: Compliant. Unit tests logic; integration tests wiring.

3. **Embeddings**  
   - `tests/test_embeddings.py`: Mix of mocked (fast) and real-model (slow+internet) tests.  
   - **Status**: Good separation; mocked tests in default unit run.

### No Redundant Removals

No tests were removed in this audit. Recommendations are for optimisation (Task 3) and consolidation where appropriate.

## Fixture Scope Policy

- **session**: Immutable resources (e.g. config, read-only fixtures).
- **module**: Per-file DB or model; reset between files.
- **function**: Mutable state; default when unsure.

## Coverage Scope

- **In scope**: `src/backend` (line and branch coverage).
- **Out of scope**: Notebooks, scripts, tooling, frontend.

## CI Pipeline

- **Fast path**: setup → lint + model-download (parallel) → test-unit. Target: <3 min for unit job.
- **Full path**: + test-performance (10 min timeout), test-integration (15 min timeout). Target: <8 min total on PR.
- **Job timeouts**: unit 5 min, performance 10 min, integration 15 min.

## Environment Matrix

| Environment | Workers | Notes |
|-------------|---------|------|
| **CI (GitHub Actions)** | `-n 2` | 2-core runners; use `--dist loadfile` |
| **Local** | `-n 4` or `min(4, cpu_count-2)` | Cap to avoid overload; document in AGENTS.md |

## References

- [TEST_TIMINGS_BASELINE.md](TEST_TIMINGS_BASELINE.md) — Baseline slow test durations
- [.github/workflows/python-ci.yml](../../.github/workflows/python-ci.yml) — CI test jobs
- [docs/technical/CI_TROUBLESHOOTING.md](../technical/CI_TROUBLESHOOTING.md) — CI issues and workarounds
