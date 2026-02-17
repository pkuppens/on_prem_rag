"""
Parameter sets for RAG configuration.

This module defines dataclasses for different parameter configurations
and provides utilities for parameter exploration and validation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ChunkingParams:
    """Parameters for document chunking."""

    chunk_size: int
    chunk_overlap: int

    def validate(self) -> list[str]:
        """
        Validate chunking parameters.

        Returns:
            List of validation error messages, empty if valid.

        """
        errors = []
        if self.chunk_size <= 0:
            errors.append("chunk_size must be positive")
        if self.chunk_overlap < 0:
            errors.append("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            errors.append("chunk_overlap must be less than chunk_size")
        return errors


@dataclass
class EmbeddingParams:
    """Parameters for text embeddings."""

    model_name: str
    cache_dir: str | None = None

    def validate(self) -> list[str]:
        """
        Validate embedding parameters.

        Returns:
            List of validation error messages, empty if valid.

        """
        errors = []
        if not self.model_name:
            errors.append("model_name must be specified")
        return errors


@dataclass
class LLMParams:
    """Parameters for LLM configuration."""

    model_name: str
    temperature: float
    max_tokens: int
    system_prompt: str | None = None

    def validate(self) -> list[str]:
        """
        Validate LLM parameters.

        Returns:
            List of validation error messages, empty if valid.

        """
        errors = []
        if not self.model_name:
            errors.append("model_name must be specified")
        if not 0 <= self.temperature <= 1:
            errors.append("temperature must be between 0 and 1")
        if self.max_tokens <= 0:
            errors.append("max_tokens must be positive")
        return errors


@dataclass
class RetrievalParams:
    """Parameters for document retrieval."""

    top_k: int
    strategy: str = "dense"  # dense | sparse | hybrid
    hybrid_alpha: float = 0.5
    use_reranker: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    use_mmr: bool = False
    mmr_lambda: float = 0.7
    rerank_candidates: int = 100

    def validate(self) -> list[str]:
        """
        Validate retrieval parameters.

        Returns:
            List of validation error messages, empty if valid.

        """
        errors = []
        if self.top_k <= 0:
            errors.append("top_k must be positive")
        if self.strategy not in ("dense", "sparse", "hybrid", "bm25"):
            errors.append("strategy must be dense, sparse, hybrid, or bm25")
        if not 0 <= self.hybrid_alpha <= 1:
            errors.append("hybrid_alpha must be between 0 and 1")
        if not 0 <= self.mmr_lambda <= 1:
            errors.append("mmr_lambda must be between 0 and 1")
        return errors


@dataclass
class RAGParams:
    """Complete set of RAG parameters."""

    chunking: ChunkingParams
    embedding: EmbeddingParams
    llm: LLMParams
    retrieval: RetrievalParams

    def validate(self) -> list[str]:
        """
        Validate all RAG parameters.

        Returns:
            List of validation error messages, empty if valid.

        """
        errors = []
        errors.extend(self.chunking.validate())
        errors.extend(self.embedding.validate())
        errors.extend(self.llm.validate())
        errors.extend(self.retrieval.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        """
        Convert parameters to dictionary format.

        Returns:
            Dictionary representation of parameters.

        """
        return {
            "chunking": {
                "chunk_size": self.chunking.chunk_size,
                "chunk_overlap": self.chunking.chunk_overlap,
            },
            "embedding": {
                "model_name": self.embedding.model_name,
                "cache_dir": self.embedding.cache_dir,
            },
            "llm": {
                "model_name": self.llm.model_name,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
                "system_prompt": self.llm.system_prompt,
            },
            "retrieval": {
                "top_k": self.retrieval.top_k,
                "strategy": self.retrieval.strategy,
                "hybrid_alpha": self.retrieval.hybrid_alpha,
                "use_reranker": self.retrieval.use_reranker,
                "reranker_model": self.retrieval.reranker_model,
                "use_mmr": self.retrieval.use_mmr,
                "mmr_lambda": self.retrieval.mmr_lambda,
                "rerank_candidates": self.retrieval.rerank_candidates,
            },
        }


# =============================================================================
# CONFIGURATION CONSTANTS WITH EXPLANATIONS
# =============================================================================

# Chunk size: Number of characters per text chunk
# - Smaller chunks (256-512): Better for precise answers, more granular retrieval
# - Larger chunks (1024-2048): Better context, may include irrelevant info
# - Rule of thumb: Match your typical question complexity
DEFAULT_CHUNK_SIZE = 512

# Chunk overlap: Characters shared between adjacent chunks
# - Prevents information loss at chunk boundaries
# - Usually 10-20% of chunk_size
# - Higher overlap = more redundancy but better context preservation
DEFAULT_CHUNK_OVERLAP = 50

# Embedding model: Converts text to vector representations
# - "BAAI/bge-small-en-v1.5": Fast, good general performance, 384 dimensions
# - "sentence-transformers/all-MiniLM-L6-v2": Lighter, 384 dimensions
# - "BAAI/bge-large-en-v1.5": Better quality, slower, 1024 dimensions
# - Choose based on speed vs accuracy tradeoff
DEFAULT_EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# Retrieval settings
# - Top-k: Number of most similar chunks to retrieve per query
# - Higher k = more context but potentially more noise
DEFAULT_TOP_K = 3

# LLM settings
DEFAULT_LLM_MODEL = "mistral"  # Ollama model name
DEFAULT_TEMPERATURE = 0.1  # Lower = more focused, higher = more creative
DEFAULT_MAX_TOKENS = 512  # Maximum response length

# Predefined parameter sets for common use cases
PRECISE_ANSWERS = RAGParams(
    chunking=ChunkingParams(
        chunk_size=256,  # Small chunks for precise matching
        chunk_overlap=25,
    ),
    embedding=EmbeddingParams(
        model_name="BAAI/bge-large-en-v1.5",  # Large model for better semantic understanding
    ),
    llm=LLMParams(
        model_name="mistral",
        temperature=0.1,  # Low temperature for precise answers
        max_tokens=512,
    ),
    retrieval=RetrievalParams(
        top_k=5,  # More context for comprehensive answers
    ),
)

CONTEXT_RICH = RAGParams(
    chunking=ChunkingParams(
        chunk_size=1024,  # Large chunks for rich context
        chunk_overlap=200,
    ),
    embedding=EmbeddingParams(
        model_name="BAAI/bge-large-en-v1.5",  # Large model for better semantic understanding
    ),
    llm=LLMParams(
        model_name="mistral",
        temperature=0.2,  # Slightly higher for more creative answers
        max_tokens=1024,
    ),
    retrieval=RetrievalParams(
        top_k=5,  # More context for comprehensive answers
    ),
)

BALANCED = RAGParams(
    chunking=ChunkingParams(
        chunk_size=512,  # Medium chunks for balanced approach
        chunk_overlap=50,
    ),
    embedding=EmbeddingParams(
        model_name="BAAI/bge-small-en-v1.5",  # Small model for speed
    ),
    llm=LLMParams(
        model_name="mistral",
        temperature=0.15,  # Balanced temperature
        max_tokens=768,
    ),
    retrieval=RetrievalParams(
        top_k=4,  # Balanced context
    ),
)

FAST_ANSWERS = RAGParams(
    chunking=ChunkingParams(
        chunk_size=512,  # Medium chunks to reduce processing
        chunk_overlap=25,  # Minimal overlap for speed
    ),
    embedding=EmbeddingParams(
        model_name="sentence-transformers/all-MiniLM-L6-v2",  # Lightweight model
    ),
    llm=LLMParams(
        model_name="mistral",
        temperature=0.2,  # Slightly higher for faster generation
        max_tokens=256,  # Shorter responses
    ),
    retrieval=RetrievalParams(
        top_k=5,  # Default to 5 results for better user experience
    ),
)

TEST_PARAMS = RAGParams(
    chunking=ChunkingParams(
        chunk_size=128,  # Small, fixed chunks for testing
        chunk_overlap=0,  # No overlap for deterministic results
    ),
    embedding=EmbeddingParams(
        model_name="sentence-transformers/all-MiniLM-L6-v2",  # Lightweight, stable model
    ),
    llm=LLMParams(
        model_name="mistral",
        temperature=0.0,  # Deterministic outputs
        max_tokens=128,  # Fixed response length
    ),
    retrieval=RetrievalParams(
        top_k=1,  # Single result for testing
    ),
)

# ---------------------------------------------------------------------------
# Parameter set lookup helpers
# ---------------------------------------------------------------------------

DEFAULT_PARAM_SET_NAME = "fast"

PARAMETER_SETS: dict[str, RAGParams] = {
    "fast": FAST_ANSWERS,
    "precise": PRECISE_ANSWERS,
    "context_rich": CONTEXT_RICH,
    "balanced": BALANCED,
    "test": TEST_PARAMS,
}


def get_param_set(name: str) -> RAGParams:
    """Return parameter set by name with fallback to default."""

    return PARAMETER_SETS.get(name, PARAMETER_SETS[DEFAULT_PARAM_SET_NAME])


def available_param_sets() -> dict[str, dict[str, Any]]:
    """Return all parameter sets as serializable dictionaries."""

    return {k: v.to_dict() for k, v in PARAMETER_SETS.items()}
