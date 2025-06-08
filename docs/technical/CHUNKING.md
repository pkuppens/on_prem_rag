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

### Current Implementation

- **Method**: LlamaIndex SimpleNodeParser
- **Chunk Size**: 512 characters (optimized for embedding model)
- **Chunk Overlap**: 50 characters
- **Metadata**: Preserved and enhanced
- **Relationships**: Tracks chunk relationships

### Alternative Approaches Considered

1. **Sentence Splitting**

   - Pros: Natural language boundaries
   - Cons: Inconsistent chunk sizes
   - Decision: Not selected due to size variability

2. **Fixed Token Count**
   - Pros: Predictable embedding costs
   - Cons: May split mid-sentence
   - Decision: Not selected due to context loss

## Implementation Details

### Integration with LlamaIndex

```python
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import Document

def process_documents(documents: list[Document], chunk_size: int = 512, chunk_overlap: int = 50):
    """Process documents into chunks with metadata and relationships."""
    node_parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        include_metadata=True,  # Preserve document metadata
        include_prev_next_rel=True,  # Track chunk relationships
    )

    # Create nodes with enhanced metadata
    nodes = node_parser.get_nodes_from_documents(documents)
    return nodes
```

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

- [src/rag_pipeline/core/chunking.py](../../src/rag_pipeline/core/chunking.py) - Main chunking implementation with SimpleNodeParser and metadata handling
- [tests/test_chunking.py](../../tests/test_chunking.py) - Comprehensive test suite covering chunking strategies, overlap, and edge cases
- [src/rag_pipeline/config/parameter_sets.py](../../src/rag_pipeline/config/parameter_sets.py) - ChunkingParams configuration and validation
- [src/rag_pipeline/core/embeddings.py](../../src/rag_pipeline/core/embeddings.py) - Integration between chunking and embedding generation
- [src/rag_pipeline/file_ingestion.py](../../src/rag_pipeline/file_ingestion.py) - File upload and chunking pipeline integration
- [src/rag_pipeline/core/rag_system.py](../../src/rag_pipeline/core/rag_system.py) - RAG system integration with chunking for index creation
