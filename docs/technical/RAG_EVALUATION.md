# RAG Evaluation Framework

Technical documentation for the batch evaluation of retrieval-augmented generation (RAG) pipelines. Supports measurable, reproducible metrics for retrieval quality and optional generation quality.

Created: 2026-02-17
Updated: 2026-02-17

## Overview

The evaluation framework enables configuration comparison (e.g. dense vs hybrid retrieval) via a single CLI command. Key use case: _"Hybrid retrieval improved MRR by 15% over dense-only"_.

## Dataset Schema

### JSON Format

The evaluation dataset is a JSON array of question-answer-context triples. Each item has:

| Field                   | Type     | Required | Description                                                  |
| ----------------------- | -------- | -------- | ------------------------------------------------------------ |
| `question`              | string   | Yes      | The query to evaluate against                                |
| `ground_truth_contexts` | string[] | Yes      | List of relevant passage texts (expected in top-k retrieval) |
| `expected_answer`       | string   | No       | Reference answer for generation metrics (LLM-as-judge)       |

### Example

```json
[
  {
    "question": "What is the ICD-10 code for type 2 diabetes?",
    "ground_truth_contexts": [
      "ICD-10 code for type 2 diabetes mellitus is E11. This code is used for non-insulin-dependent diabetes mellitus."
    ],
    "expected_answer": "E11"
  },
  {
    "question": "When should metformin be avoided?",
    "ground_truth_contexts": [
      "Metformin is contraindicated in patients with severe renal impairment (GFR < 30 mL/min).",
      "Metformin should not be used in pregnancy unless clearly necessary."
    ]
  }
]
```

### Validation Rules

- `question`: non-empty string
- `ground_truth_contexts`: non-empty array of non-empty strings
- `expected_answer`: optional; if present, non-empty string

### Matching Retrieved Chunks to Ground Truth

Retrieval metrics (Precision@k, Recall@k, MRR, Hit rate) require matching retrieved chunks to ground truth contexts. A retrieved chunk with `text` matches a ground truth context when:

- After normalization (lowercase, collapse whitespace), the shorter of the two is fully contained in the longer
- The shorter string has at least 20 characters (avoids trivial matches)

This handles chunking variations (overlap, boundaries) between the corpus and benchmark.

## Metrics

### Retrieval Metrics (no LLM required)

| Metric          | Definition                                           | Range  |
| --------------- | ---------------------------------------------------- | ------ |
| **Precision@k** | Of top-k retrieved, fraction that match ground truth | [0, 1] |
| **Recall@k**    | Of ground truth contexts, fraction found in top-k    | [0, 1] |
| **MRR**         | Mean reciprocal rank: 1/rank of first hit, 0 if none | [0, 1] |
| **Hit@k**       | 1 if any ground truth in top-k, else 0               | 0 or 1 |

### Generation Metrics (optional, requires LLM)

| Metric           | Definition                                                                 |
| ---------------- | -------------------------------------------------------------------------- |
| **Faithfulness** | Whether the answer is grounded in the retrieved context (no hallucination) |
| **Relevance**    | Whether the answer addresses the question                                  |

Generation metrics use LLM-as-judge; evaluation skips them when Ollama is unavailable.

## Usage

```bash
# Run evaluation with default configs (dense, sparse, hybrid)
uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark.json

# Specify output files
uv run evaluate-rag --dataset path/to/benchmark.json --output results/eval

# Compare specific configs
uv run evaluate-rag --dataset benchmark.json --configs dense hybrid
```

### Output

- `{output}.json`: Full results with per-query and aggregate metrics per config
- `{output}.md`: Markdown table for quick comparison

### Example Report (Markdown)

| Strategy | MRR  | Recall@5 | Hit@5 | Precision@5 |
| -------- | ---- | -------- | ----- | ----------- |
| dense    | 0.72 | 0.81     | 0.90  | 0.65        |
| hybrid   | 0.85 | 0.88     | 0.93  | 0.71        |

## Code Files

- [src/backend/rag_pipeline/evaluation/](src/backend/rag_pipeline/evaluation/) - Evaluation module
- [tests/fixtures/healthcare_benchmark.json](tests/fixtures/healthcare_benchmark.json) - Healthcare benchmark dataset
- [tests/test_evaluation_metrics.py](tests/test_evaluation_metrics.py) - Metric unit tests
- [tests/test_evaluation_dataset.py](tests/test_evaluation_dataset.py) - Schema validation tests
