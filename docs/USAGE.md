# Using the Application

This document describes how to use the on_prem_rag application: document upload, asking questions, and query search.

## Base URL

Default base URL when running via Docker: `http://localhost:9180`. Override if you changed `BACKEND_PORT` in `.env`.

## Document Upload

### Via API (file upload)

```bash
curl -X POST -F "file=@document.pdf" http://localhost:9180/api/documents/upload
```

### Via API (download from URL)

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/doc.pdf"}' \
  http://localhost:9180/api/documents/from-url
```

Supported formats: PDF, TXT, MD, DOCX, CSV, JSON. See API docs for limits.

### Via CLI (direct processing)

```bash
uv run python -m scripts.upload_documents --direct --filenameonly path/to/document.pdf
```

### List uploaded documents

```bash
curl -s http://localhost:9180/api/documents/list
```

Returns: `{"files": ["document.pdf", "synthetic-medical-doc.txt"]}`

## Asking Questions (RAG with LLM)

The `/api/ask` endpoint retrieves relevant chunks and generates an answer using the LLM. It supports multiple retrieval strategies.

### Basic request

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "When should metformin be avoided?"}' \
  http://localhost:9180/api/ask
```

### With retrieval strategy

Compare results across strategies by passing `strategy`:

```bash
# Dense (semantic search only)
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "ICD-10 code for type 2 diabetes", "strategy": "dense"}' \
  http://localhost:9180/api/ask

# Sparse (BM25 keyword search)
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "ICD-10 code for type 2 diabetes", "strategy": "sparse"}' \
  http://localhost:9180/api/ask

# Hybrid (dense + sparse merged)
curl -X POST -H "Content-Type: application/json" \
  -d '{"question": "ICD-10 code for type 2 diabetes", "strategy": "hybrid"}' \
  http://localhost:9180/api/ask
```

Valid strategies: `dense`, `sparse`, `hybrid`, `bm25`. When omitted, uses `RETRIEVAL_STRATEGY` env var or parameter set default.

### Response format

```json
{
  "answer": "The ICD-10 code for type 2 diabetes is E11...",
  "sources": [
    {
      "document_name": "synthetic-medical-doc.txt",
      "page_number": 1,
      "similarity_score": 0.95,
      "text_preview": "Chapter 1: Type 2 Diabetes Overview..."
    }
  ],
  "confidence": "high",
  "chunks_retrieved": 5,
  "average_similarity": 0.87
}
```

**Note:** `/api/ask` requires a running Ollama model. Pull with `ollama pull mistral:7b` or set `OLLAMA_MODEL` to an available model.

## Query Search (Retrieval Only)

The `/api/query` endpoint returns matching chunks without LLM generation. Uses dense (semantic) search only.

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "metformin contraindications"}' \
  http://localhost:9180/api/query
```

Optional parameters: `params_name` (parameter set), `top_k` (number of results).

**Note:** `/api/query` does not use hybrid/sparse strategies; it uses dense ChromaDB search only.

## Frontend

Open the React UI at `http://localhost:5173` (when frontend container is running). The Query page uses `/api/query` for search. Any UI that calls `/api/ask` will use the strategy parameter when provided.

## Parameter Sets

Available parameter sets (affect chunking, embedding model, top_k):

```bash
curl -s http://localhost:9180/api/parameters/sets
```

Sets: `fast`, `precise`, `context_rich`, `balanced`, `test`. Use `params_name` in requests where supported.

## Troubleshooting

| Issue                    | Remediation                                                |
| ------------------------ | ---------------------------------------------------------- |
| 503 "LLM model not available" | `ollama pull mistral:7b` or set `OLLAMA_MODEL=llama3.2:1b` |
| Empty sources            | Ensure documents are ingested; check `GET /api/documents/list` |
| Port in use              | Override `BACKEND_PORT` in `.env`; see [docs/PORTS.md](PORTS.md) |
| Invalid strategy         | Use `dense`, `sparse`, `hybrid`, or `bm25`                 |

## Related Documentation

- [docs/DEPLOYMENT.md](DEPLOYMENT.md) — Production deployment
- [docs/TEST_DOCKER.md](TEST_DOCKER.md) — Docker development
- [CLAUDE.md](../CLAUDE.md) — Build and run commands
