# Target Architecture (DDD)

This document outlines a simplified Domain-Driven Design structure for the project.
It represents the desired architecture rather than the current state.

## Domains and Bounded Contexts

| Domain                | Subdomain           | Bounded Context        |
|-----------------------|--------------------|------------------------|
| Knowledge Management  | Document Handling  | Document Processing    |
|                       | Search             | Vector Store           |
| AI Services           | LLM Integration    | LLM Provider           |
|                       | Query Resolution   | Query Service          |
| Platform              | User Interaction   | User Interface         |
|                       | Security           | Security               |
| Platform              | Deployment         | Deployment             |
| Integration           | Context Exchange   | MCP Gateway            |

## Key Entities

- **Document** – uploaded file with metadata
- **Chunk** – portion of a document for search
- **Embedding** – vector representation of a chunk
- **Query** – user question
- **Answer** – response with citations
- **User** – authenticated actor with roles
- **Role** – permissions for RBAC
- **MCPEnvelope** – context package for cross-service communication

## Directory Outline

The repository mirrors these contexts under `src/domain/`:

```
src/domain/
├── document_processing/
├── vector_store/
├── llm_provider/
├── query_service/
├── user_interface/
├── security/
├── deployment/
└── mcp_gateway/
```

Each package contains an `__init__.py` with a short description linking back to this document.
