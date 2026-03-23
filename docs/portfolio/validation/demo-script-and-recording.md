# Demo script and recording

Created: 2026-03-23
Updated: 2026-03-23

**GitHub issue (optional):** https://github.com/pkuppens/on_prem_rag/issues/88  

Use this checklist when preparing the end-to-end demo (script, OBS capture, GIF, cold start).

## Record

| Field | Value |
|-------|-------|
| Date (YYYY-MM-DD) | |
| Recorder | |
| Git commit SHA | |
| Video URL (e.g. LinkedIn / file share) | |
| GIF path (repo or asset store) | |

## Script outline (target 2–3 minutes spoken)

Tick when rehearsed.

- [ ] **Cold start** — Start stack; wait for healthy services (show or mention `/health`).
- [ ] **Upload PDF** — One representative document.
- [ ] **Text query** — One question with citations visible.
- [ ] **Source attribution** — Show how to open or read sources.
- [ ] **Voice query** — Dutch (or note if N/A).
- [ ] **Evaluation metrics** — Show or mention benchmark table / README if in scope.

## Deliverables

- [ ] Reliable from **cold start** (document exact commands used once)
- [ ] Shareable **video** suitable for LinkedIn (length, audio clarity)
- [ ] **Live demo** can be done in under 5 minutes
- [ ] **GIF** for README (15–30 s highlight) — path or link:
- [ ] **Talking points** per step (bullet list in issue comment or below)

## Cold-start repeatability

Run on a **fresh** machine or clean clone once; record blockers.

| Check | Done |
|-------|------|
| `uv sync --group dev` | [ ] |
| Env vars documented | [ ] |
| `docker-compose up` or local services | [ ] |
| First query succeeds | [ ] |

Notes:

## Out of scope

- Interactive demo tooling — not required; static script + recording only.
