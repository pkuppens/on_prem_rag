# ChromaDB Schema

The persistent Chroma vector store uses an SQLite database. Understanding
its layout helps in debugging embedding persistence and crafting advanced
queries.

The inspector utility returns a mapping of table names to their column
specifications.

Example:

```python
from rag_pipeline.utils.vector_db_inspector import inspect_chroma_schema
schema = inspect_chroma_schema("path/to/chroma")
print(schema.keys())
```

## References

- [Chroma Documentation](https://docs.trychroma.com/)

## Code Files

- [src/rag_pipeline/utils/vector_db_inspector.py](../../src/rag_pipeline/utils/vector_db_inspector.py) - SQLite schema inspection helper
- [tests/test_vector_db_inspector.py](../../tests/test_vector_db_inspector.py) - Tests verifying schema extraction
