# RAG evaluation run (issue #133)

Created: 2026-04-24
Updated: 2026-04-24

This report records **measured** retrieval metrics from a local run. It is separate from the illustrative example in [../TECHNICAL_SUMMARY.md](../TECHNICAL_SUMMARY.md). Raw CLI outputs for this run are written to `results/eval.*` and `results/eval-clinical.*` (paths are gitignored; values are copied here for the repository record).

## Reproducibility metadata

| Field | Value |
|-------|--------|
| Repository | `pkuppens/on_prem_rag` |
| Git commit (code evaluated) | `853e442a1e8890fed893936c975c7414c49d00a4` |
| Project version ([pyproject.toml](../../pyproject.toml)) | 0.1.0 |
| OS | Windows 10.0.26200 (amd64) |
| Parameter set | `fast` (see [parameter_sets.py](../../src/backend/rag_pipeline/config/parameter_sets.py)) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Chroma collection chunk count (BM25 index) | 5830 |
| Datasets | [tests/fixtures/healthcare_benchmark.json](../../tests/fixtures/healthcare_benchmark.json), [tests/fixtures/healthcare_benchmark_clinical.json](../../tests/fixtures/healthcare_benchmark_clinical.json) |
| Ingestion | `uv run fetch-healthcare-guidelines` (11 PDFs in `tmp/healthcare_guidelines`); `uv run upload-documents --direct tmp/healthcare_guidelines` (Windows logged transient path errors; vector store was already populated; re-run on a clean store if you need a clean baseline). |

## Resolved Python packages (excerpt)

Versions from `uv pip list` in the run environment:

| Package | Version |
|---------|---------|
| chromadb | 1.1.1 |
| sentence-transformers | 5.2.2 |
| torch | 2.10.0 |
| llama-index | 0.14.3 |
| llama-index-core | 0.14.14 |
| llama-index-vector-stores-chroma | 0.5.5 |

## General healthcare benchmark

Command: `uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark.json --output results/eval`

| Strategy | MRR | Recall@5 | Hit@5 | Precision@5 |
|----------|-----|----------|-------|-------------|
| dense | 0.5161 | 0.5161 | 0.5161 | 0.1032 |
| sparse | 0.8710 | 0.8710 | 0.8710 | 0.1742 |
| hybrid | 0.5898 | 0.9032 | 0.9032 | 0.1806 |

## NHG clinical benchmark (optional)

Command: `uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark_clinical.json --output results/eval-clinical`

| Strategy | MRR | Recall@5 | Hit@5 | Precision@5 |
|----------|-----|----------|-------|-------------|
| dense | 0.8833 | 1.0000 | 1.0000 | 0.4000 |
| sparse | 0.1250 | 0.1500 | 0.2000 | 0.0600 |
| hybrid | 0.5033 | 0.6000 | 0.9000 | 0.2400 |

## Notes

- Metrics depend on the ingested corpus and Chroma state; another machine or a fresh store will not match bit-for-bit without repeating ingestion.
- The README [RAG Performance](../../README.md#rag-performance) table uses the **general healthcare benchmark** numbers above to match the default `evaluate-rag` example command.
