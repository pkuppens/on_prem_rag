# Target DDD Architecture

This project is organized around a domain-driven design. The following bounded contexts define the target structure.

## Domain: Knowledge Retrieval

### Subdomains and Bounded Contexts

1. **Document Processing** – ingestion, chunking and embedding generation
2. **Vector Store** – managing embeddings and search
3. **LLM Provider** – interfacing with local LLMs
4. **Query Service** – orchestrates retrieval and answer generation
5. **Security** – authentication and role-based access

## Key Entities

| Entity | Description |
|--------|-------------|
| Document | Uploaded file metadata |
| Chunk | Text slice stored in the vector store |
| Embedding | Vector representation of a chunk |
| Query | User question to answer |
| Answer | LLM response with citations |
| User | Authenticated actor |
| Role | Permission set |

Source directories under `src/` should align to these contexts when new code is added.
