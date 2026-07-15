# Text Chunking in RAG System

## Overview

This document describes the text chunking strategy and implementation details for the RAG system. Text chunking is the process of breaking down documents into smaller, manageable pieces while preserving context and meaning.

## Table of Contents

1. [Introduction](#introduction)
2. [Chunking Strategies](#chunking-strategies)
3. [Implementation Details](#implementation-details)
4. [Performance Considerations](#performance-considerations)
5. [Future Improvements](#future-improvements)

## Introduction

Text chunking is essential for:

- Managing token limits of embedding models
- Preserving context and meaning
- Enabling efficient retrieval
- Supporting parallel processing
- Maintaining document relationships
- Ensuring data quality

## Chunking Strategies

The pipeline supports multiple strategies via the `strategy` parameter in `chunk_documents()`:

| Strategy   | Implementation        | Use case                                |
|------------|-----------------------|-----------------------------------------|
| `character`| RecursiveChunkingStrategy | Default; fixed character-based chunks   |
| `semantic` | SentenceSplitter     | Sentence boundaries; fewer mid-sentence splits |
| `recursive`| RecursiveChunkingStrategy | Same as character; alias for compatibility |

### Character (default)

- **Method**: RecursiveChunkingStrategy (paragraph, line, sentence, word boundaries)
- **Chunk Size**: 512 characters (optimized for embedding model)
- **Chunk Overlap**: 50 characters
- **Note**: Previously used SimpleNodeParser, which interprets chunk_size as tokens rather than characters and produced too few chunks for typical documents. RecursiveChunkingStrategy correctly uses character-based limits.
- **Metadata**: Preserved and enhanced

### Semantic

- **Method**: LlamaIndex SentenceSplitter
- Respects sentence and paragraph boundaries
- Reduces mid-sentence splits

### Recursive

- **Method**: Custom `RecursiveChunkingStrategy`
- Tries separators in order: `\n\n` (paragraph), `\n` (line), `. ` (sentence), ` ` (word)
- Falls back to character split when no separator fits
- Minimizes splits at unnatural boundaries

### Alternative Approaches Considered

1. **Fixed Token Count**
   - Pros: Predictable embedding costs
   - Cons: May split mid-sentence
   - Decision: Not selected due to context loss

## Implementation Details

### Integration with Chunking Strategies

The production ingestion path (used by `IngestionService`) is
`backend.ingestion.infrastructure.chunking`:

```python
from backend.ingestion.domain.value_objects import IngestionDocument
from backend.ingestion.infrastructure.chunking import chunk_documents

def process_documents(documents: list[IngestionDocument], chunk_size: int = 512, chunk_overlap: int = 50):
    """Process documents into chunks with metadata and relationships."""
    return chunk_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy="character",  # Uses RecursiveChunkingStrategy (character-based)
    )
```

A legacy, functionally equivalent `backend.rag_pipeline.core.chunking` module is
retained (not deleted) because `backend.rag_pipeline.core.embeddings` — still used by
`scripts/upload_documents.py` — depends on it (see
[on_prem_rag#178](https://github.com/pkuppens/on_prem_rag/issues/178)). New code
should use `ingestion.infrastructure.chunking`.

### Configuration

- **Chunk Size**: 512 characters
  - Optimized for embedding model's 512 token limit
  - Balances information density and retrieval accuracy
  - Smaller chunks for better semantic matching
- **Overlap**: 50 characters
  - Ensures context preservation
  - Prevents information loss at chunk boundaries
  - Optimized for embedding model efficiency

### Relationship with Embeddings

1. **Token Limits**

   - Embedding models have maximum token limits (e.g., 512 for Multilingual-E5)
   - Chunk size must be smaller than token limit
   - Character-to-token ratio varies by language

2. **Performance Impact**

   - Smaller chunks: Better semantic matching
   - Larger chunks: More context but may be truncated
   - Overlap affects embedding quality and storage

3. **Quality Considerations**
   - Chunk boundaries affect embedding quality
   - Overlap helps maintain context across chunks
   - Metadata helps track document structure

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**

   - Implement multi-threading for large documents
   - Use async processing for better resource utilization

2. **Memory Management**

   - Stream large documents
   - Implement chunking in batches

3. **Quality Control**
   - Validate chunk boundaries
   - Ensure no critical information is split
   - Track chunk relationships

## Future Improvements

### Planned Enhancements

1. **Adaptive Chunking**

   - Implement dynamic chunk sizes based on content
   - Consider semantic boundaries
   - Adjust based on embedding model capabilities

2. **Smart Overlap**

   - Adjust overlap based on content type
   - Implement semantic overlap detection
   - Optimize for different languages

3. **Data Quality**

   - Implement chunk deduplication
   - Add chunk validation rules
   - Track chunk quality metrics

4. **Metadata Enhancement**
   - Add semantic chunk summaries
   - Track cross-document relationships
   - Implement chunk versioning

## References

- [LlamaIndex Node Parser Documentation](https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/)
- [Text Chunking Best Practices](https://www.pinecone.io/learn/chunking-strategies/)
- [Embedding Model Documentation](EMBEDDING.md)

## Code Files

- [src/backend/ingestion/infrastructure/chunking.py](../../src/backend/ingestion/infrastructure/chunking.py) - Production chunking implementation (used by `IngestionService`) with RecursiveChunkingStrategy and metadata handling
- [tests/test_ingestion_chunking.py](../../tests/test_ingestion_chunking.py) - Direct test suite for the production chunking path
- [src/backend/rag_pipeline/core/chunking.py](../../src/backend/rag_pipeline/core/chunking.py) - Legacy equivalent, retained for `rag_pipeline/core/embeddings.py` (see #178)
- [tests/test_chunking.py](../../tests/test_chunking.py) - Test suite for the legacy chunking module
- [src/backend/rag_pipeline/config/parameter_sets.py](../../src/backend/rag_pipeline/config/parameter_sets.py) - ChunkingParams configuration and validation
- [src/backend/rag_pipeline/core/embeddings.py](../../src/backend/rag_pipeline/core/embeddings.py) - Integration between (legacy) chunking and embedding generation
- [src/backend/ingestion/application/ingest_service.py](../../src/backend/ingestion/application/ingest_service.py) - Production ingestion pipeline: load → chunk → embed → store
