# Scalable Architecture

Created: 2026-02-23
Updated: 2026-02-23

Architecture patterns and scaling considerations for the on-premises RAG system.

## Layered Architecture

### Routes → Services → Repositories

```
API Routes (FastAPI)
    ↓
Services (business logic, orchestration)
    ↓
Repositories / Core (data access, vector store, LLM)
```

- **Routes**: Validate input, delegate to service, return response. No business logic.
- **Services**: Orchestrate use cases (e.g. document processing, QA)
- **Repositories/Core**: Data access, external integrations (ChromaDB, Ollama)

### Bounded Contexts (DDD)

From [DOMAIN_DRIVEN_DESIGN.md](DOMAIN_DRIVEN_DESIGN.md):

| Context | Responsibility |
|---------|----------------|
| Document Processing | Load, chunk, embed |
| Vector Store | Persist embeddings, similarity search |
| LLM Provider | Local LLM interface (Ollama, etc.) |
| Query Service | Orchestrate retrieval + answer generation |
| Security | Auth, RBAC, audit |
| User Interface | React upload and chat |
| Deployment | Docker, CI/CD |

## SOLID and Dependency Injection

### Single Responsibility

- Each module has one clear job
- ChunkingService: chunk only. EmbeddingService: embed only. VectorStoreManager: store/query only.

### Open/Closed

- Extend via configuration or new implementation
- New chunking strategy = new class implementing `BaseChunker`
- New LLM backend = implement interface + register in factory

### Dependency Inversion

- Depend on abstractions (Protocol/ABC), inject concretions
- `VectorStoreManager` ABC; `ChromaVectorStoreManager` implementation
- Tests inject mocks via same interface

### Configuration Isolation

- Module behaviour via parameters, not globals
- `ChunkingConfig`, `EmbeddingConfig` dataclasses

## Modular Monolith vs Microservices

### Decision: Modular Monolith

| Approach | Pros | Cons |
|----------|------|------|
| Modular monolith | Simpler ops, single deployment, shared data | Single process scaling limit |
| Microservices | Independent scaling, team ownership | Complexity, distributed data, observability |

**Rationale**: Project size and team justify monolith. Bounded contexts give clear module boundaries. Can extract services later if needed.

## Stateless Design

- No server-side session state
- JWT carries identity; each request self-contained
- Enables horizontal scaling (multiple backend replicas)

## Horizontal Scaling Readiness

- **Stateless**: ✓
- **Shared state**: ChromaDB (external), auth tokens (external/jwt)
- **Sticky sessions**: Not required
- **Considerations**: ChromaDB can be bottleneck; vector search is CPU/GPU heavy. Scale by adding backend replicas behind load balancer.

## Features Needed at Scale (Not Yet)

Document what would be required for larger deployments:

| Feature | Purpose | When to add |
|---------|---------|-------------|
| API Gateway | Rate limit, auth, routing | Multiple clients, multi-tenant |
| Circuit breakers | Fail fast on downstream failures | Multiple external deps |
| Distributed tracing | Request flow across services | Microservices or complex pipelines |
| Message queue | Async document processing | High throughput, decoupling |
| Caching layer | Reduce embedding/LLM calls | High query volume |
| Read replicas | Scale reads | DB becomes bottleneck |

**Rationale for deferral**: Current scale does not justify. Add when metrics indicate need.

## References

- [DOMAIN_DRIVEN_DESIGN.md](DOMAIN_DRIVEN_DESIGN.md)
- [VECTOR_STORE.md](VECTOR_STORE.md)
- [.cursor/rules/modular-architecture.mdc](../../.cursor/rules/modular-architecture.mdc)
- [.cursor/rules/software-architect.mdc](../../.cursor/rules/software-architect.mdc)
