# Integration Testing with Medical Documents

**Created:** 2026-02-15  
**Purpose:** Manual/integration testing for hybrid retrieval, re-ranking, and MMR using realistic healthcare content.

**Scope:** Local testing only — not unit tests or GitHub Actions CI. See [Issue #79 plan](../../tmp/github/issue-plans/issue-79-hybrid-retrieval.md).

---

## Document Sources (Reference)

| Source Type           | Example                                   | Use Case                                      |
|-----------------------|-------------------------------------------|-----------------------------------------------|
| Drug summaries        | EMA SmPC, FDA labels (e.g. metformin)      | Exact terms, contraindications, synonyms      |
| Clinical guidelines   | NICE, ESC (type 2 diabetes, hypertension)  | Broad queries, treatment options, MMR         |
| ICD-10 / terminology  | WHO ICD-10 browser, SNOMED snippets       | Exact code retrieval, BM25 strength           |

---

## Setup

1. **Fetch documents (manual):**
   - Download 1–2 public PDFs (e.g. NICE type 2 diabetes summary, metformin SmPC excerpt)
   - Store in `tmp/integration-fixtures/medical/` (gitignored)

2. **Ingest:**
   ```bash
   uv run upload-documents tmp/integration-fixtures/medical/
   ```

3. **Query with curated questions** (see below)

---

## Curated Query Set

| Use Case              | Query                                          | Expected Behaviour                              |
|-----------------------|------------------------------------------------|-------------------------------------------------|
| Exact terminology     | "ICD-10 code for type 2 diabetes"             | BM25/hybrid returns chunks with exact code      |
| Synonym/paraphrase    | "When should metformin be avoided?"           | Dense/hybrid finds "contraindications" content  |
| Negation/safety       | "Is drug X safe in pregnancy?"                | Re-ranking places correct chunk above opposite  |
| Diversity             | "Treatment options for hypertension"          | MMR returns diet, meds, lifestyle — not dupes   |

---

## Running Integration Tests

```bash
# Slow tests (including cross-encoder re-ranking)
uv run pytest -m "slow" tests/test_retrieval_strategies.py -v

# Full integration (requires ingested medical docs)
# Run queries manually via /api/ask or REPL
```

---

## Exclusions

- No medical documents committed to the repository
- No external document fetch in unit tests or CI
- GitHub Actions continues to run fast, mocked unit tests only
