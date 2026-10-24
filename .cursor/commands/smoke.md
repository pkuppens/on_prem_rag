# Smoke: UI Smoke Test and Demo Playbook

Created: 2026-10-24

## Purpose

Walk every user-facing surface of the app in a real browser, in demo order, and report PASS/FAIL per step
with a screenshot. The same run is the demo playbook: each step below has the talking point to say while it runs.
Use it after merging a PR that touches the backend API or a UI, and before giving a demo.

`just e2e` (`scripts/e2e_smoke.py`) checks the API and runs Streamlit headlessly. This command adds the browser:
it catches defects that only show in the UI, such as a viewer that renders an error or a link to the wrong port.

## Redirect To / Used By

- **Uses**: `scripts/ui_smoke.py` (orchestration; reuses the `scripts/e2e_smoke.py` checks), `src/frontend/smoke/ui-smoke.spec.ts` (steps)
- **Used by**: run directly; after `/branch-cleanup` following a merge; before a live demo ([docs/DEMO.md](../../docs/DEMO.md))

## Run

```bash
just smoke                                   # start what is missing, run all steps, stop what it started
just smoke --headed                          # show the browser: the demo itself
just smoke --grep streamlit                  # one step
uv run python scripts/ui_smoke.py --help
```

Prerequisites: Ollama with the model from `OLLAMA_MODEL` in `.env` (`ollama list`), `uv sync --group dev`,
`cd src/frontend && npm ci && npx playwright install chromium`.

Runtime: 3-5 minutes, mostly LLM answers. Output: Playwright list report, screenshots in `tmp/debug/smoke/`,
service logs in `tmp/debug/smoke/*.log`, traces of failed steps in `tmp/debug/smoke/artifacts/`.

## Steps and talking points

| # | Step | Checks | Talking point |
|---|------|--------|---------------|
| 0 | Prerequisites | Ollama, model, backend `/api/v1/health/llm`; starts backend, Streamlit (8501), React (5173), Chainlit (8002) when missing | "Every component runs on this machine: LLM, vector store, API and three UIs. No data leaves the network." |
| 1 | React home | Backend Online badge, RAG parameter set with LLM name, light/dark theme switch | "The search UI shows which models and chunking parameters are active, so results are reproducible." |
| 2 | React upload | Drop `tests/fixtures/metformin_summary.txt`; progress row appears and clears when indexed | "Upload chunks, embeds and indexes the document locally in seconds." |
| 3 | React ask | Answer, `Sources (n)` list citing the sample, numbered citation chips, voice input button | "Every answer is grounded: the numbered chips point at the exact chunks used, with similarity scores." |
| 4 | React document viewer | Clicking source 1 renders the full document text | "Click a citation to verify the claim in the original document." |
| 5 | React chat link | Header **Chat** link points at the Chainlit app | "For conversational use there is a chat UI with voice and upload." |
| 6 | Streamlit chat | Threshold and top-k sliders, answer with expandable source naming the sample | "A minimal chat for tuning retrieval: threshold and top-k change what the LLM sees." |
| 7 | Chainlit chat | Login page renders | "The chat UI sits behind role-based login: clinicians and admins see different tools." |
| 8 | API docs | `/docs` lists `/api/v1/qa` | "Everything the UIs do is a documented REST API, so it integrates with existing hospital systems." |

## Known issues

[src/frontend/smoke/known-issues.json](../../src/frontend/smoke/known-issues.json) maps a step key to an open
GitHub issue. Those steps run as expected failures (`test.fail`) and their console errors are ignored, so a
known defect does not hide new ones and does not turn the run red.

- **Smoke finds a new defect**: raise an issue (`gh issue create --label bug --assignee @me`), add an entry
  `{ "issue": "<url>", "summary": "...", "consoleErrorPattern": "<regex, optional>" }` under the step's key,
  and mention it in the PR. A PR may merge with a known issue recorded this way.
- **Smoke reports an unexpected pass**: the defect is fixed. Remove its entry in the same PR that fixes it.

## Report

Relay per step: PASS, FAIL (with the assertion and screenshot path), or KNOWN (issue link). End with the
screenshots folder. Do not mark a run as passed when a step failed outside the known-issues list.

## Teardown

The script stops only the processes it started. Ollama, if it was started, keeps running.
