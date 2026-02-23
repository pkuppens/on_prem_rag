# Architecture Rules and Skills Mapping

Created: 2026-02-23
Updated: 2026-02-23

Mapping of Cursor/Claude rules and skills to API design, scalable architecture, and data-intensive systems competencies.

## Competency → Rules → Skills

### API Design

| Rule/Skill | Path | Key Principles |
|------------|------|----------------|
| software-architect.mdc | .cursor/rules/software-architect.mdc | API design standards, REST, versioning, integration design |
| security-best-practices.mdc | .cursor/rules/security-best-practices.mdc | Input validation, CORS, CSP, auth |
| function-definitions.mdc | .cursor/rules/function-definitions.mdc | Function design, docstrings, type hints |
| audit-logging.mdc | .cursor/rules/audit-logging.mdc | Full inputs for audit; no abbreviating |
| coding-style.mdc | .cursor/rules/coding-style.mdc | Error handling, layered architecture |

### Scalable Architecture

| Rule/Skill | Path | Key Principles |
|------------|------|----------------|
| modular-architecture.mdc | .cursor/rules/modular-architecture.mdc | Black box, single responsibility, dependency injection, Routes → Services → Repositories |
| golden-rules.mdc | .cursor/rules/golden-rules.mdc | SOLID, architecture principles |
| software-architect.mdc | .cursor/rules/software-architect.mdc | Scalability, performance, design patterns |
| code-quality-design | .cursor/skills/code-quality-design/SKILL.md | Complexity management, naming, deep modules |

### Data-Intensive Systems

| Rule/Skill | Path | Key Principles |
|------------|------|----------------|
| DOMAIN_DRIVEN_DESIGN.md | docs/technical/DOMAIN_DRIVEN_DESIGN.md | Bounded contexts, data flow |
| VECTOR_STORE.md | docs/technical/VECTOR_STORE.md | ChromaDB, alternatives, trade-offs |
| CHUNKING.md | docs/technical/CHUNKING.md | Chunking strategies |
| EMBEDDING.md | docs/technical/EMBEDDING.md | Embedding model choice |

### Testability

| Rule/Skill | Path | Key Principles |
|------------|------|----------------|
| testing.mdc | .cursor/rules/testing.mdc | Test structure, markers |
| test-documentation.mdc | .cursor/rules/test-documentation.mdc | Docstring format, business context |
| code-quality-testing | .cursor/skills/code-quality-testing/SKILL.md | Behavioral coverage, mutation-aware assertions |
| create-validation | .cursor/skills/create-validation/SKILL.md | Validation documents |
| run-validation | .cursor/skills/run-validation/SKILL.md | Execute validation |

## Quick Reference (Interview Talking Points)

- **Layered architecture**: Routes → Services → Repositories (modular-architecture.mdc)
- **Dependency injection**: Depend on abstractions; inject concretions (modular-architecture, golden-rules)
- **Bounded contexts**: Document Processing, Vector Store, Query Service, etc. (DOMAIN_DRIVEN_DESIGN)
- **Trade-offs**: ChromaDB vs Pinecone/FAISS (VECTOR_STORE); REST vs GraphQL (API_DESIGN)
- **Versioning**: v0 → v1; remove v0 after migration (API_REDESIGN)

## References

- [API_DESIGN.md](API_DESIGN.md)
- [SCALABLE_ARCHITECTURE.md](SCALABLE_ARCHITECTURE.md)
- [DATA_INTENSIVE_SYSTEMS.md](DATA_INTENSIVE_SYSTEMS.md)
