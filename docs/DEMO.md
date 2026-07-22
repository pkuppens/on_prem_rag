# End-to-End Demo Script

Created: 2026-07-22

Live demo script for `on_prem_rag`: cold start → upload → text query → source attribution →
voice query → evaluation metrics. Target runtime: 2–3 minutes for the core flow, under 5
minutes including evaluation. Written for #88; verified against a real cold-start run during
#73 (see that issue for the full verification log).

## Prerequisites

- Docker Desktop running
- `.env` present (copy from `env.example` if missing — not committed, see `.gitignore`)
- An Ollama model pulled that matches `OLLAMA_MODEL` in `.env` (default expects `mistral`;
  if you pull a tagged variant like `mistral:7b`, set `OLLAMA_MODEL=mistral:7b` to match —
  Ollama does not fall back between tags)

## Script

### 0. Cold start (~1–2 min, mostly unattended)

```bash
docker compose up -d --build
```

Talking point: *"Everything — vector store, backend, auth, frontend, and the LLM runtime —
runs in five containers on my own machine. No data leaves this network."*

Wait for backend health:
```bash
curl -s http://localhost:9180/health   # {"status":"ok"}
```

### 1. Upload a document (~15 s)

UI: open `http://localhost:5173`, drag in a PDF (e.g. a clinical guideline).
CLI equivalent for scripting/rehearsal:
```bash
curl -s -X POST http://localhost:9180/api/v1/documents \
  -F "file=@tests/fixtures/metformin_summary.txt;type=text/plain"
```

Talking point: *"Ingestion runs in the background — chunking, embedding, and vector storage —
and the UI shows live progress over a WebSocket."*

### 2. Text query with citations (~15 s)

```bash
curl -s -X POST http://localhost:9180/api/v1/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "When is metformin contraindicated?", "strategy": "hybrid"}'
```

Expect a grounded answer plus a `sources` array with `document_name`, `page_number`, and
`similarity_score`. In the UI, click the citation to jump to the source passage.

Talking point: *"Every answer is traceable — this is the difference between a chatbot and a
system a clinician or auditor can actually trust."*

### 3. Voice query (~20 s)

UI: use the microphone control, ask a question in Dutch or English.
Scripted equivalent (TTS-generated audio, same automation used to verify #73):
```bash
uv run --env-file .env python scripts/verify_voice_pipeline.py --progression
```

Talking point: *"Speech-to-text runs on-prem too, via faster-whisper — the audio never leaves
the machine either."*

### 4. Evaluation metrics (~30 s)

Requires a ingested benchmark corpus first (see `docs/HEALTHCARE_DEMO.md` for the healthcare
fixture flow) — otherwise metrics are trivially zero, which is correct behavior, not a bug.

```bash
uv run evaluate-rag --dataset tests/fixtures/healthcare_benchmark.json
```

Talking point: *"Retrieval strategy, chunk size, and embedding model are all swappable
parameters — this framework is what lets me make that choice with evidence instead of
guesswork (Precision@k, Recall@k, MRR, Hit@k)."*

## Interview talking points (summary)

- **Data sovereignty**: hybrid on-prem/cloud — same code path, swap `LLM_BACKEND` env var.
- **Architecture judgment**: retrieval strategy (dense/sparse/hybrid), chunking strategy, and
  embedding model are all explicit, swappable decisions with an evaluation framework behind
  them — not hardcoded choices.
- **Production readiness**: Kubernetes manifests, CI/CD, pre-push test enforcement, structured
  logging, health checks across all services.
- **Governance**: guardrails, auth microservice, PII detection, audit trail.
- See `docs/ENEXIS.md` for the fuller requirements-mapping version of this narrative.

## Acceptance criteria status (#88)

- [x] **Reliable from cold start** — verified via `docker compose up -d --build` +
  `scripts/verify_voice_pipeline.py --all` during #73 (found and fixed a real ingestion bug
  in the process — see #73's PR).
- [ ] **Shareable video for LinkedIn** — not produced this session; needs OBS screen capture
  (or a working browser-automation session) plus a human narrating the talking points above.
  This script is the input for that recording.
- [ ] **Live demo < 5 minutes** — script is paced for this, but timing needs to be confirmed
  against an actual run-through, not just estimated per step.

## Out of scope (per issue)

Interactive demo tooling — this is a static script plus recording, not a live demo app.
