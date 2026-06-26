"""Embedding infrastructure — generates vector embeddings for chunks.

Uses ``EmbeddingProvider`` from the LLM Gateway BC (via the domain port)
to generate embeddings, avoiding direct coupling to embedding model
implementations.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from backend.ingestion.domain.value_objects import Chunk
from backend.llm_gateway.domain.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)


def generate_embeddings(
    chunks: list[Chunk],
    embedding_provider: EmbeddingProvider,
    *,
    progress_callback: Callable[[float], None] | None = None,
) -> list[list[float]]:
    """Generate embeddings for a list of domain ``Chunk`` objects.

    Args:
        chunks: Domain ``Chunk`` objects with text to embed.
        embedding_provider: The ``EmbeddingProvider`` from LLM Gateway.
        progress_callback: Optional callback(progress 0.0-1.0).

    Returns:
        List of embedding vectors, one per non-empty chunk.
    """
    if not chunks:
        return []

    # Filter out empty chunks
    non_empty = [c for c in chunks if c.text.strip() and not c.is_empty]
    skipped = len(chunks) - len(non_empty)

    if skipped > 0:
        logger.info("Skipped %d empty chunks during embedding", skipped)

    embeddings: list[list[float]] = []

    for i, chunk in enumerate(non_empty):
        text = chunk.text.strip()
        if not text:
            continue

        try:
            embedding = embedding_provider.get_text_embedding(text)
            embeddings.append(embedding)

            if progress_callback and (i % 10 == 0 or i == len(non_empty) - 1):
                progress = (i + 1) / len(non_empty)
                progress_callback(progress)

        except Exception as e:
            logger.error("Embedding failed for chunk %d: %s", i, str(e))
            continue

    logger.debug("Generated %d embeddings", len(embeddings))
    return embeddings
