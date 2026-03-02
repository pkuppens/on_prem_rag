# Data-Intensive Systems

Created: 2026-02-23
Updated: 2026-02-23

Data flow, pipeline design, and storage patterns for the RAG system. Aligned with principles from *Designing Data-Intensive Applications* (Kleppmann).

## Document Ingestion Pipeline

### Flow

1. **Load**: DocumentLoader validates and extracts text (PDF, DOCX, etc.)
2. **Chunk**: Chunker splits text (fixed-size, semantic, or recursive)
3. **Embed**: Embedding model converts chunks to vectors
4. **Store**: VectorStoreManager persists to ChromaDB
5. **Progress**: ProgressEvent published via WebSocket (optional)

### Batch vs Streaming

| Mode | Use Case | Current |
|------|----------|---------|
| Batch | Upload N files; process sequentially | ✓ documents/upload |
| Streaming | Real-time chunking/embedding | Partial (WebSocket progress) |
| Async task | Fire-and-forget with status polling | ✓ documents_enhanced |

**Decision**: Batch is sufficient for typical upload volumes. Async task pattern (v1 upload) improves UX for large files.

## Consistency Models

- **Vector store**: ChromaDB; eventually consistent with local persistence
- **Document processing**: Sequential per file; no distributed transactions
- **Read-after-write**: Chunks available after `add_embeddings` returns; single-process, strong consistency within process

## Vector Store Design

See [VECTOR_STORE.md](VECTOR_STORE.md).

- **ChromaDB**: HNSW index, cosine similarity
- **Dimensions**: 1024 (embedding model)
- **Metadata**: Document name, page, chunk index
- **Alternatives considered**: Pinecone (cloud), FAISS (complexity) — see VECTOR_STORE.md

## Chunking Strategies

See [CHUNKING.md](CHUNKING.md).

| Strategy | Trade-off |
|----------|-----------|
| Character/recursive | Predictable size; may split mid-sentence |
| Semantic | Sentence boundaries; more computation |
| Page-based | Respects PDF pages; variable chunk sizes |

**Decision**: RecursiveChunkingStrategy (512 chars, 50 overlap) for balance of quality and simplicity.

## Embedding Model Choice

See [EMBEDDING.md](EMBEDDING.md).

- **Model**: Multilingual-E5-large-instruct
- **Trade-offs**: Quality vs size; multilingual vs English-only
- **On-premises**: Must run locally; no API calls

## Literature References

| Source | Relevance |
|--------|-----------|
| *Designing Data-Intensive Applications* (Kleppmann) | Storage, replication, consistency, batch vs stream |
| *Building Elasticsearch* | Search and indexing (vector search analogous) |
| LlamaIndex docs | Chunking, embedding, retrieval patterns |

## References

- [VECTOR_STORE.md](VECTOR_STORE.md)
- [CHUNKING.md](CHUNKING.md)
- [EMBEDDING.md](EMBEDDING.md)
- [DOMAIN_DRIVEN_DESIGN.md](DOMAIN_DRIVEN_DESIGN.md)
