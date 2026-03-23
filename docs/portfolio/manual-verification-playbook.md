# Manual verification playbook

Created: 2026-03-23
Updated: 2026-03-23

This playbook covers **human** verification, **demo evidence**, and **sign-off** for environment-dependent runs. It does not replace automated tests in CI; it adds repeatable checklists and places to record evidence.

## Templates

| Goal | Template |
|------|----------|
| MVP flow: upload → query → voice | [validation/mvp-end-to-end-flow-verification.md](./validation/mvp-end-to-end-flow-verification.md) |
| Portfolio demo: script, recording, cold start | [validation/demo-script-and-recording.md](./validation/demo-script-and-recording.md) |
| Load testing and RAG benchmark runs | [validation/load-testing-and-rag-evaluation-signoff.md](./validation/load-testing-and-rag-evaluation-signoff.md) |
| Portfolio MVP completion (epic closure) | [validation/mvp-portfolio-completion-checklist.md](./validation/mvp-portfolio-completion-checklist.md) |

GitHub tracking (optional): issues for [MVP verification](https://github.com/pkuppens/on_prem_rag/issues/73), [demo](https://github.com/pkuppens/on_prem_rag/issues/88), [load tests](https://github.com/pkuppens/on_prem_rag/issues/129), [evaluation](https://github.com/pkuppens/on_prem_rag/issues/133), [epic](https://github.com/pkuppens/on_prem_rag/issues/91).

## How to use

1. Copy the relevant template to `tmp/` or duplicate it into a dated file under `docs/portfolio/validation/reports/` **only if** you want committed evidence (optional).
2. Run steps in order; check boxes.
3. Paste a short summary into the GitHub issue or link to the committed report.

## References

- [api-v1-delivery-sequence.md](./api-v1-delivery-sequence.md)
- [ISSUES_README.md](./ISSUES_README.md)
