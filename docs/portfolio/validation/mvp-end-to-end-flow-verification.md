# MVP end-to-end flow verification

Created: 2026-03-23
Updated: 2026-04-06

**Verification ID:** VERIFY-MVP-FLOW  
**RTM (primary):** Step 1 → **VAL-UR-001** / **VAL-SR-001**; Step 2 → **VAL-UR-002** / **VAL-SR-002**; Step 3 (voice) → **VAL-UR-004** — see [requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md](../../requirements/REQUIREMENTS_TRACEABILITY_MATRIX.md).  
**GitHub issue (optional):** https://github.com/pkuppens/on_prem_rag/issues/73  

Copy this file to `tmp/validation-YYYYMMDD-mvp-flow.md` for a run, or save a filled copy under `docs/portfolio/validation/reports/` if you commit evidence.

## Record

| Field | Value |
|-------|-------|
| Date (YYYY-MM-DD) | |
| Tester | |
| Git commit SHA | |
| Branch or tag | |
| Docker / local | |
| Frontend URL used | |

## Preconditions

- [ ] `docker-compose up` (or documented stack) running
- [ ] Backend `/health` returns OK
- [ ] Test PDF available (clinical guideline or sample)

## Step 1 — Document upload

1. Open the React UI (or Chainlit) at the configured URL.
2. Upload a PDF.
3. Wait until ingestion completes (progress via WebSocket if applicable).

**Pass criteria:** Document appears in the list; no blocking errors.

- [ ] Pass / [ ] Fail — Notes:

## Step 2 — Text query

1. Enter a question about the uploaded document.
2. Submit the query.

**Pass criteria:** Answer returned with source citations; sources identify document and page/section.

- [ ] Pass / [ ] Fail — Notes:

## Step 3 — Voice query (if STT available)

1. Use microphone input.
2. Speak a question (Dutch or English).
3. Submit transcribed query.

**Pass criteria:** Transcription shown; answer with sources; latency acceptable (under 5 seconds for STT + response if applicable).

- [ ] Pass / [ ] Fail — N/A — Notes:

## Step 4 — Source attribution

1. Confirm each answer includes visible or clickable source references.
2. Open or view source text (sidebar or modal).

**Pass criteria:** User can trace the answer to the original document/section.

- [ ] Pass / [ ] Fail — Notes:

## Acceptance criteria (mirror for GitHub)

- [ ] Upload → ingest → list flow works
- [ ] Query returns cited answer
- [ ] Voice pipeline works (or marked N/A with reason)
- [ ] Source attribution is clear and usable
- [ ] Non-technical person can complete flow with these instructions

## Verdict

- [ ] **PASS** — Ready for demo recording
- [ ] **FAIL** — Open bugs: (link issues)

## Evidence (optional)

- Screenshots path:
- Screen recording link:
