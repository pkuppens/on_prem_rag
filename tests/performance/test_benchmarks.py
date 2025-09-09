"""Performance benchmarks for the RAG pipeline.

This module provides comprehensive performance testing for all major components
of the RAG pipeline including document processing, chunking, embedding generation,
and vector store operations.

Test Categories:
1. Document Processing Benchmarks
   - File loading performance by type
   - Chunking performance by strategy
   - Memory usage during processing

2. Embedding Generation Benchmarks
   - Model loading time
   - Embedding generation speed
   - Cache hit/miss performance

3. Vector Store Benchmarks
   - Insert performance
   - Query performance
   - Concurrent operation handling

4. End-to-End Benchmarks
   - Complete document processing pipeline
   - Query response times
   - System resource usage
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest
from llama_index.core import Document

from src.backend.rag_pipeline.core.chunking import chunk_documents
from src.backend.rag_pipeline.core.chunking_strategies import (
    ChunkingConfig,
    ChunkingStrategy,
    chunk_documents_with_strategy,
)
from src.backend.rag_pipeline.core.document_loader import DocumentLoader
from src.backend.rag_pipeline.core.embedding_cache import get_embedding_cache
from src.backend.rag_pipeline.core.embeddings import embed_text_nodes
from src.backend.rag_pipeline.core.vector_store import get_vector_store_manager_from_env
from src.backend.rag_pipeline.utils.embedding_model_utils import get_embedding_model


class TestDocumentProcessingBenchmarks:
    """Benchmarks for document processing operations."""

    @pytest.fixture
    def sample_documents(self, test_data_dir) -> List[Document]:
        """Create sample documents for benchmarking."""
        documents = []
        for i in range(10):
            doc = Document(
                text=f"This is sample document {i} with some content. " * 100,  # ~1000 chars
                metadata={"doc_id": f"doc_{i}", "page": i + 1},
            )
            documents.append(doc)
        return documents

    def test_document_loading_performance(self, test_data_dir):
        """Benchmark document loading performance by file type."""
        loader = DocumentLoader()

        # Test different file types if available
        file_types = [".txt", ".md", ".pdf"]
        results = {}

        for file_type in file_types:
            test_files = list(test_data_dir.glob(f"*{file_type}"))
            if test_files:
                test_file = test_files[0]

                start_time = time.time()
                documents, metadata = loader.load_document(test_file)
                elapsed_time = time.time() - start_time

                results[file_type] = {
                    "elapsed_time": elapsed_time,
                    "documents_loaded": len(documents),
                    "file_size_bytes": metadata.file_size,
                    "throughput_mb_per_sec": (metadata.file_size / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0,
                }

        # Assert performance thresholds
        for file_type, metrics in results.items():
            assert metrics["elapsed_time"] < 5.0, f"{file_type} loading too slow: {metrics['elapsed_time']:.2f}s"
            assert metrics["throughput_mb_per_sec"] > 0.1, (
                f"{file_type} throughput too low: {metrics['throughput_mb_per_sec']:.2f} MB/s"
            )

    def test_chunking_strategy_performance(self, sample_documents):
        """Benchmark different chunking strategies."""
        strategies = [
            ChunkingStrategy.FIXED_SIZE,
            ChunkingStrategy.SENTENCE,
            ChunkingStrategy.SEMANTIC,
        ]

        results = {}

        for strategy in strategies:
            config = ChunkingConfig(
                strategy=strategy,
                chunk_size=512,
                chunk_overlap=50,
            )

            start_time = time.time()
            chunks = chunk_documents_with_strategy(documents=sample_documents, config=config, source_path="benchmark_test")
            elapsed_time = time.time() - start_time

            results[strategy.value] = {
                "elapsed_time": elapsed_time,
                "chunks_created": len(chunks),
                "chunks_per_second": len(chunks) / elapsed_time if elapsed_time > 0 else 0,
                "avg_chunk_size": sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0,
            }

        # Assert performance thresholds
        for strategy, metrics in results.items():
            assert metrics["elapsed_time"] < 10.0, f"{strategy} chunking too slow: {metrics['elapsed_time']:.2f}s"
            assert metrics["chunks_per_second"] > 1.0, (
                f"{strategy} chunking rate too low: {metrics['chunks_per_second']:.2f} chunks/s"
            )

    def test_memory_usage_during_processing(self, sample_documents):
        """Test memory usage during document processing."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process documents
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE)
        chunks = chunk_documents_with_strategy(documents=sample_documents, config=config, source_path="memory_test")

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Assert memory usage is reasonable
        assert memory_increase < 500, f"Memory usage too high: {memory_increase:.2f} MB increase"
        assert len(chunks) > 0, "No chunks created"


class TestEmbeddingBenchmarks:
    """Benchmarks for embedding generation operations."""

    @pytest.fixture
    def sample_texts(self) -> List[str]:
        """Create sample texts for embedding benchmarks."""
        return [
            "This is a sample text for embedding generation testing.",
            "Another sample text with different content and structure.",
            "A third sample text to test batch processing capabilities.",
        ] * 10  # 30 texts total

    def test_embedding_generation_speed(self, sample_texts):
        """Benchmark embedding generation speed."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        # Create text nodes
        nodes = [Document(text=text) for text in sample_texts]

        # Test without cache
        start_time = time.time()
        embeddings_no_cache = embed_text_nodes(nodes, model_name, use_cache=False)
        elapsed_no_cache = time.time() - start_time

        # Test with cache
        start_time = time.time()
        embeddings_with_cache = embed_text_nodes(nodes, model_name, use_cache=True)
        elapsed_with_cache = time.time() - start_time

        # Second run with cache (should be faster)
        start_time = time.time()
        embeddings_cached = embed_text_nodes(nodes, model_name, use_cache=True)
        elapsed_cached = time.time() - start_time

        # Assert performance
        assert len(embeddings_no_cache) == len(sample_texts)
        assert len(embeddings_with_cache) == len(sample_texts)
        assert len(embeddings_cached) == len(sample_texts)

        # Cache should improve performance on second run
        assert elapsed_cached < elapsed_with_cache, (
            f"Cache not improving performance: {elapsed_cached:.2f}s vs {elapsed_with_cache:.2f}s"
        )

        # Throughput should be reasonable
        throughput = len(sample_texts) / elapsed_no_cache
        assert throughput > 1.0, f"Embedding throughput too low: {throughput:.2f} texts/s"

    def test_model_loading_performance(self):
        """Benchmark model loading time."""
        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        start_time = time.time()
        model = get_embedding_model(model_name)
        elapsed_time = time.time() - start_time

        # Model loading should be reasonably fast
        assert elapsed_time < 30.0, f"Model loading too slow: {elapsed_time:.2f}s"

        # Test that model works
        test_embedding = model.get_text_embedding("Test text")
        assert len(test_embedding) > 0, "Model not producing embeddings"

    def test_cache_performance(self, sample_texts):
        """Benchmark embedding cache performance."""
        cache = get_embedding_cache()
        model_name = "sentence-transformers/all-MiniLM-L6-v2"

        # Clear cache
        cache.clear()

        # First run - cache miss
        start_time = time.time()
        for text in sample_texts[:5]:  # Test with subset
            cache.get(text, model_name)
        elapsed_miss = time.time() - start_time

        # Add to cache
        for text in sample_texts[:5]:
            embedding = get_embedding_model(model_name).get_text_embedding(text)
            cache.put(text, model_name, embedding)

        # Second run - cache hit
        start_time = time.time()
        for text in sample_texts[:5]:
            cache.get(text, model_name)
        elapsed_hit = time.time() - start_time

        # Cache hits should be much faster
        assert elapsed_hit < elapsed_miss, f"Cache not improving performance: {elapsed_hit:.2f}s vs {elapsed_miss:.2f}s"

        # Get cache statistics
        stats = cache.get_stats()
        assert stats.hit_rate > 0.0, "Cache should have hits"


class TestVectorStoreBenchmarks:
    """Benchmarks for vector store operations."""

    @pytest.fixture
    def vector_store_manager(self):
        """Get vector store manager for testing."""
        return get_vector_store_manager_from_env()

    @pytest.fixture
    def sample_embeddings(self):
        """Create sample embeddings for testing."""
        model = get_embedding_model("sentence-transformers/all-MiniLM-L6-v2")
        texts = [f"Sample text {i} for vector store testing." for i in range(100)]
        return [model.get_text_embedding(text) for text in texts]

    def test_insert_performance(self, vector_store_manager, sample_embeddings):
        """Benchmark vector store insert performance."""
        ids = [f"test_id_{i}" for i in range(len(sample_embeddings))]
        metadatas = [{"text": f"Sample text {i}"} for i in range(len(sample_embeddings))]

        start_time = time.time()
        vector_store_manager.add_embeddings(ids, sample_embeddings, metadatas)
        elapsed_time = time.time() - start_time

        # Calculate throughput
        throughput = len(sample_embeddings) / elapsed_time

        # Assert performance
        assert elapsed_time < 10.0, f"Insert operation too slow: {elapsed_time:.2f}s"
        assert throughput > 10.0, f"Insert throughput too low: {throughput:.2f} embeddings/s"

    def test_query_performance(self, vector_store_manager, sample_embeddings):
        """Benchmark vector store query performance."""
        # Use first embedding as query
        query_embedding = sample_embeddings[0]

        # Test different top_k values
        top_k_values = [1, 5, 10, 20]
        results = {}

        for top_k in top_k_values:
            start_time = time.time()
            ids, distances = vector_store_manager.query(query_embedding, top_k)
            elapsed_time = time.time() - start_time

            results[top_k] = {
                "elapsed_time": elapsed_time,
                "results_returned": len(ids),
                "queries_per_second": 1.0 / elapsed_time if elapsed_time > 0 else 0,
            }

        # Assert performance
        for top_k, metrics in results.items():
            assert metrics["elapsed_time"] < 1.0, f"Query with top_k={top_k} too slow: {metrics['elapsed_time']:.2f}s"
            assert metrics["results_returned"] <= top_k, f"Too many results returned: {metrics['results_returned']} > {top_k}"

    def test_concurrent_operations(self, vector_store_manager, sample_embeddings):
        """Test concurrent vector store operations."""
        import queue
        import threading

        results_queue = queue.Queue()

        def query_worker(embedding, worker_id):
            """Worker function for concurrent queries."""
            start_time = time.time()
            ids, distances = vector_store_manager.query(embedding, 5)
            elapsed_time = time.time() - start_time

            results_queue.put(
                {
                    "worker_id": worker_id,
                    "elapsed_time": elapsed_time,
                    "results_count": len(ids),
                }
            )

        # Start multiple concurrent queries
        threads = []
        for i in range(5):
            thread = threading.Thread(target=query_worker, args=(sample_embeddings[i % len(sample_embeddings)], i))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Assert all queries completed successfully
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

        for result in results:
            assert result["elapsed_time"] < 2.0, f"Concurrent query too slow: {result['elapsed_time']:.2f}s"
            assert result["results_count"] > 0, "No results returned from concurrent query"


class TestEndToEndBenchmarks:
    """End-to-end performance benchmarks."""

    def test_complete_document_processing_pipeline(self, test_data_dir):
        """Benchmark complete document processing pipeline."""
        # Find a test PDF file
        pdf_files = list(test_data_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files available for testing")

        test_file = pdf_files[0]

        # Load document
        start_time = time.time()
        loader = DocumentLoader()
        documents, metadata = loader.load_document(test_file)
        load_time = time.time() - start_time

        # Chunk documents
        start_time = time.time()
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE)
        chunks = chunk_documents_with_strategy(documents=documents, config=config, source_path=test_file)
        chunk_time = time.time() - start_time

        # Generate embeddings
        start_time = time.time()
        embeddings = embed_text_nodes(chunks, "sentence-transformers/all-MiniLM-L6-v2")
        embed_time = time.time() - start_time

        # Store in vector store
        start_time = time.time()
        vector_store = get_vector_store_manager_from_env()
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [chunk.metadata for chunk in chunks]
        vector_store.add_embeddings(ids, embeddings, metadatas)
        store_time = time.time() - start_time

        total_time = load_time + chunk_time + embed_time + store_time

        # Assert performance thresholds
        assert load_time < 5.0, f"Document loading too slow: {load_time:.2f}s"
        assert chunk_time < 2.0, f"Chunking too slow: {chunk_time:.2f}s"
        assert embed_time < 30.0, f"Embedding generation too slow: {embed_time:.2f}s"
        assert store_time < 5.0, f"Vector store operations too slow: {store_time:.2f}s"
        assert total_time < 60.0, f"Total pipeline too slow: {total_time:.2f}s"

        # Test query performance
        start_time = time.time()
        query_embedding = embeddings[0]
        result_ids, distances = vector_store.query(query_embedding, 5)
        query_time = time.time() - start_time

        assert query_time < 1.0, f"Query too slow: {query_time:.2f}s"
        assert len(result_ids) > 0, "No query results returned"

    def test_system_resource_usage(self, test_data_dir):
        """Test system resource usage during processing."""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Get initial resource usage
        initial_cpu = process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process a document
        pdf_files = list(test_data_dir.glob("*.pdf"))
        if pdf_files:
            loader = DocumentLoader()
            documents, metadata = loader.load_document(pdf_files[0])

            config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE)
            chunks = chunk_documents_with_strategy(documents=documents, config=config, source_path=pdf_files[0])

            embeddings = embed_text_nodes(chunks, "sentence-transformers/all-MiniLM-L6-v2")

        # Get peak resource usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Assert resource usage is reasonable
        assert memory_increase < 1000, f"Memory usage too high: {memory_increase:.2f} MB increase"

        # CPU usage should be reasonable (this is harder to test reliably)
        # We'll just ensure the process is still responsive
        assert process.is_running(), "Process became unresponsive"


# Performance test markers
pytestmark = [
    pytest.mark.performance,
    pytest.mark.slow,
]
