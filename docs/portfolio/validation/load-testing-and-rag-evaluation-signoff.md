# Load testing and RAG evaluation sign-off

Created: 2026-03-23
Updated: 2026-04-24

Automation should already ship **scripts and documentation**. This template is for **human execution** before release or portfolio sign-off when results are environment-dependent.

## Load testing

**Docs:** [scripts/load/README.md](../../../scripts/load/README.md), [TESTABILITY.md](../../technical/TESTABILITY.md)  
**GitHub issue (optional):** https://github.com/pkuppens/on_prem_rag/issues/129

| Field | Value |
|-------|-------|
| Date (YYYY-MM-DD) | |
| Operator | |
| Git commit SHA | |
| Tool (k6 / locust / other) | |
| Target base URL | |

### Steps

- [ ] Read `scripts/load/README.md` and use the documented command for the key endpoint (e.g. `POST /api/.../ask` after v1 is merged).
- [ ] Record approximate **throughput** and **latency** (p50/p95 if available).
- [ ] Compare to **target SLOs** documented next to the script or in TESTABILITY.

### Sign-off

- [ ] Run completed without fatal errors
- [ ] Results noted (paste below or attach)

Notes:

---

## RAG evaluation

**References:** [TECHNICAL_SUMMARY.md](../../TECHNICAL_SUMMARY.md), and the GitHub issue for evaluation (exact `uv run` commands). **Measured run (versions, SHAs):** [rag-evaluation-run-2026-04-24.md](../../reports/rag-evaluation-run-2026-04-24.md).  
**GitHub issue (optional):** https://github.com/pkuppens/on_prem_rag/issues/133

| Field | Value |
|-------|-------|
| Date (YYYY-MM-DD) | |
| Operator | |
| Git commit SHA | |
| Machine notes (GPU, Ollama, etc.) | |

### Steps (adjust if the issue body changes)

- [ ] `uv run fetch-healthcare-guidelines` (if used)
- [ ] `uv run upload-documents --direct tmp/healthcare_guidelines` (or per issue)
- [ ] `uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark.json --output results/eval`
- [ ] Optional clinical benchmark if available
- [ ] Update README performance table from `results/eval.md` (or attach numbers)

### Outputs

- [ ] `results/eval.json` and `results/eval.md` present with real metrics
- [ ] README RAG Performance table updated
- [ ] Failures or environment notes documented in issue comment

Notes:
