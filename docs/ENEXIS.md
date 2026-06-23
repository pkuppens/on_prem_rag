# Enexis Senior AI Engineer — Demo Reference

This document maps the `on_prem_rag` project to the Enexis Senior AI Engineer role requirements.
It serves as a leave-behind reference after a live demo session.

---

## Project in One Sentence

`on_prem_rag` is a production-ready, hybrid on-premises/cloud RAG platform that demonstrates
the full lifecycle from PoC architecture to deployable service — with built-in evaluation,
governance, and extensibility patterns.

---

## Mapping to Enexis Requirements

### 1. LLM, RAG & Evaluation Architecture

The core is a **generic RAG module** with explicit architecture decisions (ADRs) for every
major trade-off:

**Retrieval strategies** (`src/backend/rag_pipeline/core/retrieval.py`):
- Dense retrieval: ChromaDB vector search with configurable embedding models
- Sparse retrieval: BM25 keyword search (`bm25_store.py`)
- **Hybrid retrieval**: Reciprocal Rank Fusion (RRF) merging dense + sparse ranked lists
  — outperforms either alone, especially for domain-specific terminology

**Chunking strategies** (`src/backend/rag_pipeline/core/chunking.py`):
- Character-based, sentence-based, and semantic chunking via Strategy pattern
- Key trade-off: chunk size vs. retrieval precision vs. context window cost
- Overlap management preserves context across chunk boundaries

**Embedding models** (`src/backend/rag_pipeline/core/embeddings.py`):
- Configurable: local HuggingFace models (data stays on-prem) or cloud APIs
- Trade-off: `all-MiniLM-L6-v2` (fast, small) vs. larger domain-specific models

**LLM providers** (`src/backend/rag_pipeline/core/llm_providers.py`):
- Provider-agnostic via LiteLLM: Ollama (local), OpenAI, **Azure OpenAI**, Anthropic, HuggingFace
- Switch via `LLM_BACKEND` + `LLM_MODEL` env vars — no code changes required
- Enables the Enexis pattern: local Ollama for dev/air-gapped, Azure OpenAI for production

**Evaluation framework** (`src/backend/rag_pipeline/evaluation/`):
- Metrics: Precision@k, Recall@k, MRR, Hit@k — `metrics.py`
- Benchmark runner with healthcare fixture dataset — `runner.py`
- CLI entrypoint: `uv run evaluate-rag --dataset <benchmark.json>`
- Enables systematic comparison of retrieval strategies, chunk sizes, embedding models

---

### 2. Production-Ready Platform Components

**Kubernetes deployment** (`k8s/`):
All services are containerized and deployable via Kustomize:
- `namespace.yaml`, `configmap.yaml`, `secret.yaml` — environment isolation
- `backend.yaml`, `auth.yaml`, `frontend.yaml` — microservice deployments
- `chroma.yaml`, `ollama.yaml` — stateful AI/vector services
- `ingress.yaml` — single entrypoint with routing

This is the on-prem equivalent of an AKS deployment — the same manifests run on Azure
Kubernetes Service with minimal changes (swap `ollama` for Azure OpenAI endpoint).

**CI/CD pipeline** (`.github/workflows/python-ci.yml`):
- Runs on every PR and push to `main`
- Custom CI base image (GHCR) with pre-loaded HuggingFace models — avoids 10-min model downloads
- Parallel test matrix: unit, integration, slow, internet-gated markers
- Pre-push test enforcement via git hooks (`scripts/setup_git_hooks.py`)
- Concurrency control: newer run cancels older in-progress run on same ref

**Observability**:
- Structured logging throughout (`StructuredLogger` wrapper)
- Health check endpoints on all providers
- Audit trail service (`src/backend/audit_trail/`)

---

### 3. Governance, Security & Compliance

**Authentication & authorization** (`src/backend/auth_service/`):
- Dedicated OAuth2/JWT auth microservice, separate from the RAG backend
- Role-based access control (`src/backend/access_control/`)

**NeMo Guardrails** (`src/backend/guardrails/`):
- Input and output guardrails as middleware
- Configurable guardrail policies via `config_loader.py`
- Prevents prompt injection, PII leakage, off-topic responses

**PII detection** (`src/backend/privacy_guard/`):
- Scans documents before indexing
- Relevant for Enexis: grid operator data often contains personal/address information

---

### 4. Cloud & Infrastructure

| Concern | Implementation |
|---|---|
| LLM provider | LiteLLM abstraction — `azure` backend selectable via env var |
| Container orchestration | Kubernetes manifests (`k8s/`) — AKS-compatible |
| CI/CD | GitHub Actions with custom GHCR container images |
| Secrets management | Kubernetes `secret.yaml` + environment injection |
| Storage backends | ChromaDB (default), extensible to Postgres/Supabase/SQLite |
| IaC pattern | Kustomize overlays for environment-specific config |

The hybrid design intentionally mirrors Azure's recommended pattern for regulated environments:
sensitive data processed locally, LLM inference routed to Azure OpenAI when approved.

---

### 5. Extensibility: MCP & Agentic Patterns

**Model Context Protocol server** (`src/mcp_calendar/`):
- MCP server exposing Google Calendar as tools/resources/prompts
- Demonstrates the agentic integration pattern: LLM + external tool via standardized protocol
- Directly applicable to Enexis use cases: scheduling, asset management systems as MCP tools

**Agent memory** (`src/backend/memory/`):
- Long-term and shared memory backed by ChromaDB
- Enables multi-turn agentic workflows

---

### 6. Engineering Culture & Knowledge Transfer

The project is structured to be maintainable and transferable by a team — not just its author:

- **CLAUDE.md** — onboarding document for AI-assisted development workflows
- **`.cursor/rules/`** — codified architecture rules and coding standards (ADR-style)
- **Pre-commit hooks** — automated format/lint enforcement before every commit
- **Comprehensive test markers** — clear distinction between fast unit tests and slow/external tests
- **`docs/technical/`** — 20+ technical decision documents covering chunking, embedding, CI, async patterns

This mirrors the Enexis requirement: *"hoogwaardige documentatie van architectuur, ontwerpkeuzes,
runbooks en best practices, zodat oplossingen overdraagbaar en beheersbaar zijn."*

---

## Suggested Demo Flow (45–60 min)

1. **Architecture overview** (10 min) — whiteboard the hybrid on-prem/cloud design, provider abstraction
2. **Live RAG query** (10 min) — ingest a document, run a query, show retrieved chunks + answer
3. **Retrieval trade-offs** (10 min) — switch dense → sparse → hybrid, compare results
4. **Evaluation run** (5 min) — `uv run evaluate-rag`, walk through Precision@k / MRR numbers
5. **Guardrails demo** (5 min) — show input guardrail blocking a prompt injection attempt
6. **MCP / agentic** (5 min) — show MCP calendar server as a tool integration pattern
7. **Production path** (5 min) — `k8s/` manifests, CI pipeline, monitoring hooks

---

## Key ADRs & Trade-offs to Discuss

| Decision | Options considered | Choice | Rationale |
|---|---|---|---|
| Retrieval strategy | Dense only / Sparse only / Hybrid | Hybrid (RRF) | Best recall for domain docs with jargon |
| Chunking | Character / Sentence / Semantic | Configurable (Strategy pattern) | No single best — benchmark per corpus |
| LLM provider | Hardcoded / Factory / LiteLLM | LiteLLM abstraction | Cloud-agnostic, one-line provider switch |
| Vector DB | Pinecone / Weaviate / ChromaDB | ChromaDB | On-prem, no SaaS dependency, AKS-mountable |
| Auth | Inline / Sidecar / Separate service | Separate OAuth2 microservice | Separation of concerns, replaceable |
