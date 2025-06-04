"""
Parameter exploration utilities for RAG configuration.

This module provides tools for exploring different parameter combinations
and evaluating their impact on RAG performance.
"""

from dataclasses import dataclass
from itertools import product
from typing import Any

from .parameter_sets import (
    BALANCED,
    CONTEXT_RICH,
    PRECISE_ANSWERS,
    ChunkingParams,
    EmbeddingParams,
    LLMParams,
    RAGParams,
    RetrievalParams,
)


@dataclass
class ParameterRange:
    """Define a range of values for a parameter."""

    name: str
    values: list[Any]
    description: str


def explore_chunking_params(
    chunk_sizes: list[int] = [256, 512, 1024],
    overlap_ratios: list[float] = [0.1, 0.2, 0.3],
) -> list[tuple[ChunkingParams, str]]:
    """
    Generate chunking parameter combinations.

    Args:
        chunk_sizes: List of chunk sizes to try
        overlap_ratios: List of overlap ratios (0-1) to try

    Returns:
        List of (ChunkingParams, description) tuples

    """
    combinations = []
    for size in chunk_sizes:
        for ratio in overlap_ratios:
            overlap = int(size * ratio)
            params = ChunkingParams(chunk_size=size, chunk_overlap=overlap)
            desc = f"size={size}, overlap={overlap} ({ratio:.0%})"
            combinations.append((params, desc))
    return combinations


def explore_embedding_params(
    models: list[str] = [
        "BAAI/bge-small-en-v1.5",
        "sentence-transformers/all-MiniLM-L6-v2",
        "BAAI/bge-large-en-v1.5",
    ],
) -> list[tuple[EmbeddingParams, str]]:
    """
    Generate embedding parameter combinations.

    Args:
        models: List of embedding model names to try

    Returns:
        List of (EmbeddingParams, description) tuples

    """
    return [(EmbeddingParams(model_name=m), f"model={m}") for m in models]


def explore_llm_params(
    temperatures: list[float] = [0.1, 0.2, 0.3],
    max_tokens: list[int] = [512, 768, 1024],
) -> list[tuple[LLMParams, str]]:
    """
    Generate LLM parameter combinations.

    Args:
        temperatures: List of temperature values to try
        max_tokens: List of max token values to try

    Returns:
        List of (LLMParams, description) tuples

    """
    combinations = []
    for temp in temperatures:
        for tokens in max_tokens:
            params = LLMParams(
                model_name="mistral",
                temperature=temp,
                max_tokens=tokens,
            )
            desc = f"temp={temp}, max_tokens={tokens}"
            combinations.append((params, desc))
    return combinations


def explore_retrieval_params(
    top_k_values: list[int] = [3, 4, 5],
) -> list[tuple[RetrievalParams, str]]:
    """
    Generate retrieval parameter combinations.

    Args:
        top_k_values: List of top-k values to try

    Returns:
        List of (RetrievalParams, description) tuples

    """
    return [(RetrievalParams(top_k=k), f"top_k={k}") for k in top_k_values]


def generate_parameter_grid(
    chunk_sizes: list[int] | None = None,
    overlap_ratios: list[float] | None = None,
    embedding_models: list[str] | None = None,
    temperatures: list[float] | None = None,
    max_tokens: list[int] | None = None,
    top_k_values: list[int] | None = None,
) -> list[tuple[RAGParams, str]]:
    """
    Generate a grid of parameter combinations.

    Args:
        chunk_sizes: Optional list of chunk sizes to try
        overlap_ratios: Optional list of overlap ratios to try
        embedding_models: Optional list of embedding models to try
        temperatures: Optional list of temperature values to try
        max_tokens: Optional list of max token values to try
        top_k_values: Optional list of top-k values to try

    Returns:
        List of (RAGParams, description) tuples

    """
    # Use default values if not specified
    chunking = explore_chunking_params(chunk_sizes, overlap_ratios)
    embedding = explore_embedding_params(embedding_models)
    llm = explore_llm_params(temperatures, max_tokens)
    retrieval = explore_retrieval_params(top_k_values)

    # Generate all combinations
    combinations = []
    for (c, c_desc), (e, e_desc), (llm_params, llm_desc), (r, r_desc) in product(
        chunking, embedding, llm, retrieval
    ):
        params = RAGParams(
            chunking=c,
            embedding=e,
            llm=llm_params,
            retrieval=r,
        )
        desc = f"Chunking: {c_desc} | Embedding: {e_desc} | LLM: {llm_desc} | Retrieval: {r_desc}"
        combinations.append((params, desc))

    return combinations


# Predefined parameter sets for quick access
PREDEFINED_SETS = {
    "precise": PRECISE_ANSWERS,
    "context_rich": CONTEXT_RICH,
    "balanced": BALANCED,
}
