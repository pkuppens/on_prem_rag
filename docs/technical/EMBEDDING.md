# Embeddings in RAG System

## Overview

This document describes the embedding strategy and implementation details for the RAG (Retrieval-Augmented Generation) system, focusing on on-premises deployment and multilingual support.

## Table of Contents

1. [Introduction](#introduction)
2. [Embedding Models](#embedding-models)
3. [Implementation Details](#implementation-details)
4. [Performance Considerations](#performance-considerations)
5. [Future Improvements](#future-improvements)

## Introduction

Embeddings are vector representations of text that capture semantic meaning. In our RAG system, they are crucial for:

- Converting text chunks into searchable vectors
- Enabling semantic search capabilities
- Supporting similarity matching for document retrieval
- Ensuring data privacy through on-premises deployment

## Embedding Models

### Current Implementation

- **Model**: Multilingual-E5-large-instruct
- **Dimensions**: 1024
- **Max Tokens**: 512
- **Languages**: 100+ languages
- **License**: MIT
- **Size**: 560M parameters

### Model Selection Criteria

1. **On-Premises Requirement**

   - Must be deployable locally
   - No external API dependencies
   - Open source license

2. **Multilingual Support**

   - Support for multiple languages
   - Good performance across languages
   - Consistent quality

3. **Performance**
   - Adequate for retrieval tasks
   - Reasonable resource requirements
   - Sentence-transformers compatible

### Alternative Models Considered

1. **gte-Qwen2-7B-instruct**

   - Pros: Strong performance, 7B parameters
   - Cons: Larger resource requirements
   - Decision: Not selected due to size

2. **Linq-Embed-Mistral**
   - Pros: Good performance, smaller size
   - Cons: Limited language support
   - Decision: Not selected due to language coverage

## Implementation Details

### Integration with LlamaIndex

```python
# Example implementation using LlamaIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

def setup_embeddings(model_name: str, cache_dir: str) -> HuggingFaceEmbedding:
    """Setup local embedding model with caching."""
    return HuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=cache_dir
    )

# Configure global settings
Settings.embed_model = setup_embeddings(
    model_name="intfloat/multilingual-e5-large-instruct",
    cache_dir="data/embeddings_cache"
)
```

### Retrieving Embedding Models

Use `get_embedding_model` to load models from a local directory, existing cache,
or download from Hugging Face if needed. The function respects the
`TRANSFORMERS_OFFLINE` environment variable for offline testing.

**In-process cache:** The model is loaded once per `(model_name, cache_dir)` and
reused for all subsequent calls. This keeps the model hot in memory and avoids the
~20–30 s cold-start per document during batch ingestion. First document in a batch
pays the load cost; later documents reuse the cached instance.

```python
from backend.rag_pipeline.utils.embedding_model_utils import get_embedding_model

embed_model = get_embedding_model(
    "sentence-transformers/all-MiniLM-L6-v2",
    cache_dir="data/cache/huggingface",
)
```

To clear the cache (e.g. when switching models or freeing memory):

```python
from backend.rag_pipeline.utils.embedding_model_utils import clear_embedding_model_cache

clear_embedding_model_cache()
```

### Document Processing and Embedding

```python
from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SimpleNodeParser

def process_documents(documents: list[Document], chunk_size: int = 512, chunk_overlap: int = 50):
    """Process documents and create embeddings."""
    # Parse documents into nodes with metadata
    node_parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        include_metadata=True,
        include_prev_next_rel=True
    )

    # Create nodes and generate embeddings
    nodes = node_parser.get_nodes_from_documents(documents)

    # Create vector index
    index = VectorStoreIndex(nodes)
    return index
```

### Querying with Embeddings

```python
def query_documents(index: VectorStoreIndex, question: str, top_k: int = 5):
    """Query documents using embeddings."""
    query_engine = index.as_query_engine(
        similarity_top_k=top_k,
        response_mode="compact"
    )

    response = query_engine.query(question)

    # Extract results with source information
    result = {
        "answer": str(response),
        "sources": []
    }

    if hasattr(response, "source_nodes"):
        for i, node in enumerate(response.source_nodes):
            source_info = {
                "rank": i + 1,
                "score": getattr(node, "score", 0.0),
                "reference": node.metadata.get("full_reference", "Unknown"),
                "content_preview": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                "metadata": dict(node.metadata)
            }
            result["sources"].append(source_info)

    return result
```

### Configuration

- **Token Limit**: 512 tokens per input
- **Batch Size**: 32 (default)
- **Normalization**: L2 normalization
- **Task Instructions**: Required for queries

### Token Limit Impact

The 512 token limit affects our system in several ways:

1. **Chunking Strategy**: Documents must be chunked to fit within 512 tokens
2. **Processing Pipeline**:
   - Text extraction → Chunking (max 512 tokens) → Embedding
   - Overlap between chunks to maintain context
3. **Performance Trade-offs**:
   - Smaller chunks: Better token efficiency
   - Larger chunks: More context but may be truncated

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**

   - Group multiple texts for efficient processing
   - Implement parallel processing where possible

2. **Caching**

   - Cache embeddings for frequently accessed documents
   - Implement LRU cache with configurable size

3. **Error Handling**
   - Implement retry logic for failed embeddings
   - Log failed embeddings for manual review

## Future Improvements

### Planned Enhancements

1. **Model Updates**

   - Monitor for newer embedding models
   - Evaluate performance improvements
   - Consider task-specific fine-tuning

2. **Task-Specific Optimization**

   - Investigate legal document embeddings
   - Optimize for retrieval tasks
   - Add domain-specific training

3. **Performance**
   - Implement model quantization
   - Add support for GPU acceleration
   - Optimize batch processing

## References

- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [Multilingual-E5 Documentation](https://huggingface.co/intfloat/multilingual-e5-large-instruct)
- [Sentence Transformers Documentation](https://www.sbert.net/)

## Code Files

- [src/rag_pipeline/core/embeddings.py](../../src/rag_pipeline/core/embeddings.py) - Embedding generation and query utilities
- [tests/test_embedding_shapes.py](../../tests/test_embedding_shapes.py) - Tests for embedding vector dimensions
- [src/backend/rag_pipeline/utils/embedding_model_utils.py](../../src/backend/rag_pipeline/utils/embedding_model_utils.py) - Helper to load embedding models from cache or download
- [tests/test_embedding_model_utils.py](../../tests/test_embedding_model_utils.py) - Tests for model retrieval logic
