# Vector Store in RAG System

## Overview

This document describes the vector store implementation and configuration for the RAG system. The vector store is responsible for storing and retrieving document embeddings efficiently.

## Table of Contents

1. [Introduction](#introduction)
2. [Vector Store Selection](#vector-store-selection)
3. [Implementation Details](#implementation-details)
4. [Performance Considerations](#performance-considerations)
5. [Future Improvements](#future-improvements)

## Introduction

The vector store is crucial for:

- Storing document embeddings
- Enabling fast similarity search
- Supporting efficient retrieval
- Managing metadata
- Ensuring data quality
- Tracking processing progress

## Vector Store Selection

### Current Implementation

- **Database**: Chroma
- **Dimensions**: 1024 (matching embedding model)
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Distance Metric**: Cosine Similarity
- **Metadata Support**: Rich document metadata
- **Progress Tracking**: Integrated with chunking

### Alternative Solutions Considered

1. **Pinecone**

   - Pros: Managed service, high performance
   - Cons: Cost, vendor lock-in
   - Decision: Not selected due to on-premises requirement

2. **FAISS**
   - Pros: High performance, Facebook-backed
   - Cons: Complex setup, maintenance overhead
   - Decision: Not selected due to complexity

## Implementation Details

### ChromaDB Setup

```python
import chromadb
from chromadb.config import Settings

def setup_vector_store():
    """Setup ChromaDB vector store with persistence."""
    client = chromadb.Client(Settings(
        persist_directory="data/chroma",
        anonymized_telemetry=False
    ))
    collection = client.create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )
    return collection
```

### Integration with Progress Tracking

```python
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.chroma import ChromaVectorStore
from typing import Callable, List

def create_index_with_progress(
    documents: List[Document],
    progress_callback: Callable[[str, float], None],
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> VectorStoreIndex:
    """Create vector index with progress tracking."""
    # Step 1: Document Chunking (30% of total work)
    progress_callback("Chunking documents...", 0.0)
    node_parser = SimpleNodeParser.from_defaults(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        include_metadata=True,
        include_prev_next_rel=True
    )
    nodes = node_parser.get_nodes_from_documents(documents)
    progress_callback("Documents chunked", 0.3)

    # Step 2: Deduplication (20% of total work)
    progress_callback("Deduplicating chunks...", 0.3)
    unique_nodes = deduplicate_nodes(nodes)
    progress_callback("Chunks deduplicated", 0.5)

    # Step 3: Embedding Generation (40% of total work)
    progress_callback("Generating embeddings...", 0.5)

    # Setup ChromaDB storage
    chroma_client = chromadb.Client(Settings(
        persist_directory="data/chroma",
        anonymized_telemetry=False
    ))
    chroma_collection = chroma_client.get_or_create_collection(
        name="documents",
        metadata={"hnsw:space": "cosine"}
    )

    # Create vector store with ChromaDB
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Create index with progress tracking
    index = VectorStoreIndex(
        nodes=unique_nodes,
        storage_context=storage_context,
        show_progress=True
    )
    progress_callback("Embeddings generated", 0.9)

    # Step 4: Index Finalization (10% of total work)
    progress_callback("Finalizing index...", 0.9)
    index.storage_context.persist()
    progress_callback("Index created successfully", 1.0)

    return index

def deduplicate_nodes(nodes: List[Node]) -> List[Node]:
    """Remove duplicate nodes based on content and metadata."""
    seen_contents = set()
    unique_nodes = []

    for node in nodes:
        # Create a unique identifier based on content and key metadata
        content_hash = hash(node.text)
        metadata_hash = hash(frozenset({
            k: v for k, v in node.metadata.items()
            if k in ['filename', 'page_label', 'chunk_id']
        }.items()))
        node_hash = (content_hash, metadata_hash)

        if node_hash not in seen_contents:
            seen_contents.add(node_hash)
            unique_nodes.append(node)

    return unique_nodes
```

### Migration from Default Storage

To migrate from the default storage to ChromaDB:

1. **Setup ChromaDB**

   - Install ChromaDB: `pip install chromadb`
   - Configure persistence directory
   - Create collection with appropriate settings

2. **Migration Steps**

   - Export existing embeddings and metadata
   - Create new ChromaDB collection
   - Import data with progress tracking
   - Verify data integrity
   - Update storage context configuration

3. **Configuration Updates**
   - Update vector store settings
   - Configure persistence
   - Set up metadata handling
   - Enable progress tracking

### Configuration

- **Persistence**: Local file system
- **Index Parameters**:
  - M: 16 (connections per node)
  - ef_construction: 100
  - ef_search: 50
- **Metadata Storage**: SQLite with enhanced schema
- **Progress Tracking**: WebSocket events

### Metadata Management

1. **Document Metadata**

   - Original file information
   - Page numbers and sections
   - Creation and modification dates
   - Document relationships

2. **Chunk Metadata**

   - Chunk identifiers
   - Position in document
   - Relationship to other chunks
   - Processing status

3. **Quality Metadata**
   - Embedding quality scores
   - Deduplication status
   - Validation results

## Performance Considerations

### Optimization Strategies

1. **Indexing**

   - Regular index optimization
   - Batch updates for better performance
   - Progress tracking for long operations

2. **Query Optimization**

   - Implement query caching
   - Use approximate nearest neighbor search
   - Metadata-based filtering

3. **Resource Management**
   - Monitor memory usage
   - Implement cleanup routines
   - Handle large document sets

## Future Improvements

### Planned Enhancements

1. **Scalability**

   - Implement sharding
   - Add support for distributed deployment
   - Optimize for large document sets

2. **Performance**

   - Optimize index parameters
   - Implement advanced caching
   - Add batch processing capabilities

3. **Features**

   - Add support for hybrid search
   - Implement metadata filtering
   - Enhance progress tracking

4. **Data Quality**
   - Improve deduplication algorithms
   - Add content validation
   - Implement quality metrics

## References

- [Chroma Documentation](https://docs.trychroma.com/)
- [Vector Database Comparison](https://www.pinecone.io/learn/vector-database/)
- [LlamaIndex Storage Documentation](https://docs.llamaindex.ai/en/stable/module_guides/storage/)
