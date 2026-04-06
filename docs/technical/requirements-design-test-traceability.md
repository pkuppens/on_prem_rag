# Requirements, design, and test traceability (lightweight)

Created: 2026-03-23
Updated: 2026-04-06

Use this pattern when work touches code or APIs so **requirements**, **design**, and **verification** stay aligned without heavy process overhead.

**Product-wide matrix:** For numbered engineering requirements (UR / SR / SSR) and roll-up validation IDs (**VAL-UR-***, **VAL-SR-***, **VAL-SSR-***), see [requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md](../requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md) and [requirements/README.md](../requirements/README.md). Per-change mini-matrices below still apply; reference a **VAL-SR-*** (or UR/SSR) row when a change maps to an existing requirement.

## Levels (maps to SDLC)

| Arm | Artefact | Typical location |
|-----|----------|------------------|
| Requirements | GitHub issue acceptance criteria | Issue body |
| Architecture / design | Gap analysis, OpenAPI, endpoint tables | `docs/technical/` (e.g. [API_REDESIGN.md](API_REDESIGN.md)) |
| Implementation | Code | `src/` |
| Unit verification | Fast pytest | `tests/` |
| Integration verification | API or service tests | `tests/` |
| Performance / characterisation | Load scripts, eval runs | `scripts/load/`, `results/` (if committed) |

## Mini matrix (per change)

For each change set, add a short block (issue comment or subsection in a design doc):

```markdown
## Traceability

| Requirement (AC) | Design reference | Verification |
|------------------|------------------|--------------|
| (quote checkbox) | `docs/technical/...` section or OpenAPI path | `tests/test_....py::test_...` or manual step ID |
```

## Rules

- **One row per acceptance criterion** (or split complex ACs).
- If verification is **manual**, point to a step in [manual-verification-playbook.md](../portfolio/manual-verification-playbook.md) or a file under `docs/portfolio/validation/`.
- **Retrofit:** When you change files without prior design docs, add the missing design paragraph in the same PR.

## References

- [api-v1-delivery-sequence.md](../portfolio/api-v1-delivery-sequence.md)
- [ISSUE_IMPLEMENTATION_WORKFLOW.md](../portfolio/ISSUE_IMPLEMENTATION_WORKFLOW.md)
