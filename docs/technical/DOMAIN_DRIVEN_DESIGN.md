# Domain Driven Design: On-Premises RAG Solution

## Domain Overview

The system ingests enterprise documents and makes them searchable through a
Retrieval‑Augmented Generation workflow. It exposes a web API and UI for
questions, returning answers with source citations. The architecture prioritizes
local execution and security. **The latest iteration adopts the Model‑Context‑Protocol (MCP) to standardize how context is packaged and transferred between services.**

## Bounded Contexts

- **Document Processing** – loaders, chunking and embeddings
- **Vector Store** – manages document chunks and search
- **LLM Provider** – abstraction over Ollama, llama.cpp and others
- **Query Service** – combines retrieval and LLM answer generation
- **User Interface** – React frontend for upload and chat
- **Security** – authentication, authorization and audit logging
- **Deployment** – Docker, monitoring and CI/CD
- **MCP Gateway** – handles Model‑Context‑Protocol envelopes between components

## Key Entities

| Entity    | Description                                    |
|-----------|------------------------------------------------|
| Document  | Uploaded file with metadata                    |
| Chunk     | Portion of a document stored for search        |
| Embedding | Vector representation of a chunk               |
| Query     | User question to be answered                   |
| Answer    | LLM response with citations                    |
| User      | Authenticated actor with roles                 |
| Role      | Permission set used by RBAC                    |
| MCPEnvelope | Standardized package of model, context and metadata |

## Component Responsibilities

- **DocumentLoader** – validates and extracts text
- **Chunker** – splits text using configured strategy
- **Embeddings** – generates vectors via sentence transformers
- **VectorStoreManager** – stores and retrieves embeddings
- **LLMProviderFactory** – creates provider instances
- **SecurityManager** – JWT handling and role enforcement
- **Web API** – FastAPI endpoints and streaming responses
- **MCPAdapter** – converts internal data structures to MCP envelopes
- **Frontend** – React components for upload and Q&A

## Data Flow

1. User uploads document through the UI.
2. Backend processes file into chunks and embeddings.
3. **MCPAdapter** packages the processed data into an MCP envelope.
4. Embeddings stored in ChromaDB via VectorStoreManager.
5. User submits question to `/ask` endpoint using an MCP formatted request.
6. Query Service retrieves relevant chunks.
7. LLMProvider generates answer using context from the MCP envelope.
8. Response streamed back as an MCP envelope with citations.

## References

- [docs/technical/CHUNKING.md](docs/technical/CHUNKING.md)
- [docs/technical/EMBEDDING.md](docs/technical/EMBEDDING.md)
- [docs/technical/LLM.md](docs/technical/LLM.md)
- [docs/technical/VECTOR_STORE.md](docs/technical/VECTOR_STORE.md)
- [Model‑Context‑Protocol Introduction](https://modelcontextprotocol.io/introduction)

## Code Files

- [src/backend/rag_pipeline/file_ingestion.py](src/backend/rag_pipeline/file_ingestion.py) – High‑level file processing API
- [src/backend/rag_pipeline/core/vector_store.py](src/backend/rag_pipeline/core/vector_store.py) – ChromaDB integration
- [src/backend/rag_pipeline/core/embeddings.py](src/backend/rag_pipeline/core/embeddings.py) – Embedding generation
- [src/backend/security/security_manager.py](src/backend/security/security_manager.py) – JWT utilities
- [src/backend/mcp/mcp_adapter.py](src/backend/mcp/mcp_adapter.py) – MCP envelope utilities *(planned)*
