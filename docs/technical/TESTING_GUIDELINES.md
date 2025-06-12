# Testing Guidelines for Vector Stores and Embeddings

## Vector Store Testing Strategy

### Persistent vs In-Memory Trade-offs

#### Persistent Vector Stores (Recommended)

**Pros:**

- Reuses expensive embeddings across test runs
- Realistic testing with same storage mechanism as production
- Consistent, reproducible results
- Good for integration and performance testing

**Cons:**

- Requires cleanup management
- May have stale data after model changes
- Takes disk space

#### In-Memory Vector Stores

**Pros:**

- Always fresh data
- No cleanup needed
- Fast test startup

**Cons:**

- Expensive embedding regeneration every run
- May behave differently than production
- Difficult to debug persistence issues

### Recommended Approach: Hybrid Strategy

```python
# Use persistent stores for expensive integration tests
@pytest.mark.slow
@pytest.mark.integration
def test_full_pipeline_with_persistence(test_case_dir):
    """Use persistent storage for expensive integration tests."""
    result = embed_chunks(
        chunking_result,
        model_name,
        persist_dir=test_case_dir / "embeddings",
        collection_name="integration_test"
    )

# Use in-memory for quick unit tests
@pytest.mark.unit
def test_query_interface():
    """Use lightweight mocking for interface tests."""
    # Mock the embedding generation
    with patch('rag_pipeline.core.embeddings.HuggingFaceEmbedding') as mock_embed:
        mock_embed.return_value.get_text_embedding.return_value = [0.1, 0.2, 0.3]
        # Test interface without expensive embeddings
```

### Test Isolation Best Practices

#### 1. Unique Test Directories

```python
@pytest.fixture
def test_case_dir(tmp_path):
    """Create isolated directory for each test case."""
    return tmp_path / f"test_{uuid.uuid4()}"
```

#### 2. Collection Name Isolation

```python
def test_with_unique_collection(test_case_dir):
    collection_name = f"test_{uuid.uuid4()}"
    # Each test gets its own collection
```

#### 3. Cleanup Strategy

```python
@pytest.fixture
def clean_vector_store(test_case_dir):
    """Clean vector store after test."""
    yield test_case_dir
    # Cleanup code here if needed
    if test_case_dir.exists():
        shutil.rmtree(test_case_dir)
```

### Handling Model Changes

When embedding models or chunking parameters change:

#### 1. Version-aware Test Data

```python
def get_test_collection_name(model_name: str, chunk_size: int) -> str:
    """Create version-specific collection names."""
    model_hash = hashlib.md5(model_name.encode()).hexdigest()[:8]
    return f"test_{model_hash}_{chunk_size}"
```

#### 2. Test Data Validation

```python
def validate_test_embeddings(persist_dir: Path, expected_model: str) -> bool:
    """Check if existing embeddings match expected model."""
    metadata_file = persist_dir / "test_metadata.json"
    if not metadata_file.exists():
        return False

    with open(metadata_file) as f:
        metadata = json.load(f)

    return metadata.get("model_name") == expected_model
```

#### 3. Conditional Regeneration

```python
def ensure_fresh_embeddings(persist_dir: Path, model_name: str):
    """Regenerate embeddings if model changed."""
    if not validate_test_embeddings(persist_dir, model_name):
        # Clear old embeddings
        if persist_dir.exists():
            shutil.rmtree(persist_dir)

        # Will be regenerated on next test run
```

### Test Categories

#### Fast Tests (< 1 second)

- Interface validation
- Mocked embedding tests
- Configuration testing
- Error handling

#### Medium Tests (1-10 seconds)

- Small document processing
- Single-page PDFs
- Query functionality with cached embeddings

#### Slow Tests (10+ seconds)

- Full document integration
- Large PDF processing
- Multi-document collections
- Performance benchmarks

### Example Test Structure

```python
class TestEmbeddingPipeline:
    """Organized test class with different test types."""

    @pytest.mark.unit
    def test_embedding_interface(self):
        """Fast unit test with mocking."""
        pass

    @pytest.mark.integration
    def test_small_document_pipeline(self, test_case_dir):
        """Medium test with 1-page document."""
        pass

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_pipeline_performance(self, test_case_dir):
        """Slow test with full document and persistence."""
        pass
```

### Running Tests Efficiently

```bash
# Run only fast tests during development
pytest -m "not slow"

# Run integration tests
pytest -m "integration"

# Run all tests including slow ones
pytest -m "slow or not slow"
```

### Debugging Vector Store Issues

#### 1. Inspect Collections

```python
def debug_collection_contents(persist_dir: Path, collection_name: str):
    """Helper to inspect vector store contents."""
    from rag_pipeline.utils.vector_db_inspector import inspect_chroma_schema

    schema = inspect_chroma_schema(persist_dir)
    print(f"Collections: {schema['collections']}")

    # Additional debugging...
```

#### 2. Validate Embeddings

```python
def validate_embedding_quality(embeddings: list[list[float]]) -> dict:
    """Check embedding quality metrics."""
    return {
        "count": len(embeddings),
        "dimensions": len(embeddings[0]) if embeddings else 0,
        "avg_magnitude": np.mean([np.linalg.norm(emb) for emb in embeddings])
    }
```

## Key Takeaways

1. **Use persistent stores for expensive integration tests**
2. **Use unique directories/collections for test isolation**
3. **Implement version-aware collection naming**
4. **Clean up test data appropriately**
5. **Separate fast unit tests from slow integration tests**
6. **Mock expensive operations when testing interfaces**
7. **Validate test data freshness after model changes**
