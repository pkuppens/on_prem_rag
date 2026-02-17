#!/usr/bin/env python3
"""Diagnostic script for Chroma vector store.

Checks: document count, embedding model consistency, stored document names.
Run from project root. For Docker: docker-compose exec backend python scripts/diagnose_chroma.py
"""

from __future__ import annotations

import os
import sys

# Ensure project is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from backend.rag_pipeline.config.vector_store import VectorStoreConfig
from backend.rag_pipeline.core.vector_store import ChromaVectorStoreManager


def main() -> int:
    print("=== Chroma Diagnostic ===\n")
    config = VectorStoreConfig()
    print(f"CHROMA_HOST: {config.host}")
    print(f"CHROMA_PORT: {config.port}")
    print(f"Collection: {config.collection_name}")
    print()

    manager = ChromaVectorStoreManager(config)
    coll = manager._collection

    count = coll.count()
    print(f"Total chunks in collection: {count}")

    if count == 0:
        print("\n*** Collection is EMPTY. No documents have been embedded. ***")
        print("Upload a document via POST /api/documents/upload and wait ~30s for processing.")
        return 1

    # Get param set used for upload and retrieval
    params = get_param_set(DEFAULT_PARAM_SET_NAME)
    embed_model = params.embedding.model_name
    print(f"\nEmbedding model (store + retrieve): {embed_model}")

    # Sample documents to see document_name values
    result = coll.get(include=["metadatas", "documents"], limit=min(100, count))
    metadatas = result.get("metadatas") or []
    documents = result.get("documents") or []

    doc_names: set[str] = set()
    for m in metadatas:
        if isinstance(m, dict) and "document_name" in m:
            doc_names.add(m["document_name"])

    print(f"\nDocument names in collection ({len(doc_names)} unique):")
    for name in sorted(doc_names):
        print(f"  - {name}")

    # Check embedding dimension
    sample = coll.get(limit=1, include=["embeddings"])
    emb_list = sample.get("embeddings")
    if emb_list is not None and len(emb_list) > 0:
        first_emb = emb_list[0]
        if first_emb is not None and hasattr(first_emb, "__len__"):
            dim = len(first_emb)
            print(f"\nEmbedding dimension: {dim}")
            expected = {
                "sentence-transformers/all-MiniLM-L6-v2": 384,
                "BAAI/bge-small-en-v1.5": 384,
                "BAAI/bge-large-en-v1.5": 1024,
            }
            exp_dim = expected.get(embed_model)
            if exp_dim and dim != exp_dim:
                print(f"  WARNING: Expected {exp_dim} for {embed_model}, got {dim}")

    # Sample first chunk text
    if documents:
        print(f"\nSample chunk (first 200 chars):")
        print(f"  {repr((documents[0] or '')[:200])}")

    print("\n=== Diagnostic complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
