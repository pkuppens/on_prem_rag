"""Configurable chunking strategies for the RAG pipeline.

This module provides different chunking strategies that can be selected based on
document type, content, and use case requirements.

See docs/technical/CHUNKING.md for detailed strategy comparisons and use cases.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from llama_index.core import Document
from llama_index.core.node_parser import (
    CodeSplitter,
    HTMLNodeParser,
    MarkdownNodeParser,
    SemanticSplitterNodeParser,
    SentenceSplitter,
    SimpleNodeParser,
)
from llama_index.core.schema import BaseNode

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    CODE = "code"
    MARKDOWN = "markdown"
    HTML = "html"
    HYBRID = "hybrid"


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies."""

    strategy: ChunkingStrategy
    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_length: int = 10
    max_chunk_length: int = 2048
    # Semantic-specific parameters
    buffer_size: int = 1
    breakpoint_percentile_threshold: float = 95.0
    # Code-specific parameters
    language: str = "python"
    # Hybrid parameters
    semantic_ratio: float = 0.3  # 30% semantic, 70% fixed-size


class BaseChunkingStrategy(ABC):
    """Base class for chunking strategies."""

    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.logger = StructuredLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using this strategy.

        Args:
            documents: List of documents to chunk
            **kwargs: Additional strategy-specific parameters

        Returns:
            List of chunked nodes
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy."""
        pass


class FixedSizeChunkingStrategy(BaseChunkingStrategy):
    """Fixed-size chunking strategy using SimpleNodeParser."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using fixed-size strategy."""
        self.logger.debug(
            "Using fixed-size chunking",
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            num_documents=len(documents),
        )

        parser = SimpleNodeParser.from_defaults(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "fixed_size"


class SemanticChunkingStrategy(BaseChunkingStrategy):
    """Semantic chunking strategy using SemanticSplitterNodeParser."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using semantic strategy."""
        self.logger.debug(
            "Using semantic chunking",
            buffer_size=self.config.buffer_size,
            breakpoint_threshold=self.config.breakpoint_percentile_threshold,
            num_documents=len(documents),
        )

        # Get embedding model from kwargs or use default
        embed_model = kwargs.get("embed_model")
        if not embed_model:
            from ..utils.embedding_model_utils import get_embedding_model

            embed_model = get_embedding_model("sentence-transformers/all-MiniLM-L6-v2")

        parser = SemanticSplitterNodeParser(
            buffer_size=self.config.buffer_size,
            breakpoint_percentile_threshold=self.config.breakpoint_percentile_threshold,
            embed_model=embed_model,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "semantic"


class SentenceChunkingStrategy(BaseChunkingStrategy):
    """Sentence-based chunking strategy."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using sentence-based strategy."""
        self.logger.debug(
            "Using sentence-based chunking",
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            num_documents=len(documents),
        )

        parser = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "sentence"


class CodeChunkingStrategy(BaseChunkingStrategy):
    """Code-specific chunking strategy."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using code-specific strategy."""
        self.logger.debug(
            "Using code chunking", language=self.config.language, chunk_size=self.config.chunk_size, num_documents=len(documents)
        )

        parser = CodeSplitter(
            language=self.config.language,
            chunk_lines=self.config.chunk_size // 50,  # Approximate lines per chunk
            chunk_lines_overlap=self.config.chunk_overlap // 50,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "code"


class MarkdownChunkingStrategy(BaseChunkingStrategy):
    """Markdown-specific chunking strategy."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using markdown-specific strategy."""
        self.logger.debug("Using markdown chunking", chunk_size=self.config.chunk_size, num_documents=len(documents))

        parser = MarkdownNodeParser(
            chunk_size=self.config.chunk_size,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "markdown"


class HTMLChunkingStrategy(BaseChunkingStrategy):
    """HTML-specific chunking strategy."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using HTML-specific strategy."""
        self.logger.debug("Using HTML chunking", chunk_size=self.config.chunk_size, num_documents=len(documents))

        parser = HTMLNodeParser(
            chunk_size=self.config.chunk_size,
        )

        return parser.get_nodes_from_documents(documents)

    def get_strategy_name(self) -> str:
        return "html"


class HybridChunkingStrategy(BaseChunkingStrategy):
    """Hybrid chunking strategy combining semantic and fixed-size approaches."""

    def chunk_documents(self, documents: list[Document], **kwargs) -> list[BaseNode]:
        """Chunk documents using hybrid strategy."""
        self.logger.debug(
            "Using hybrid chunking",
            semantic_ratio=self.config.semantic_ratio,
            chunk_size=self.config.chunk_size,
            num_documents=len(documents),
        )

        # Get embedding model for semantic chunking
        embed_model = kwargs.get("embed_model")
        if not embed_model:
            from ..utils.embedding_model_utils import get_embedding_model

            embed_model = get_embedding_model("sentence-transformers/all-MiniLM-L6-v2")

        # First, do semantic chunking
        semantic_parser = SemanticSplitterNodeParser(
            buffer_size=self.config.buffer_size,
            breakpoint_percentile_threshold=self.config.breakpoint_percentile_threshold,
            embed_model=embed_model,
        )
        semantic_chunks = semantic_parser.get_nodes_from_documents(documents)

        # Then, apply fixed-size chunking to large semantic chunks
        fixed_parser = SimpleNodeParser.from_defaults(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
        )

        final_chunks = []
        for chunk in semantic_chunks:
            if len(chunk.text) > self.config.max_chunk_length:
                # Re-chunk large semantic chunks
                temp_doc = Document(text=chunk.text, metadata=chunk.metadata)
                sub_chunks = fixed_parser.get_nodes_from_documents([temp_doc])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        return final_chunks

    def get_strategy_name(self) -> str:
        return "hybrid"


class ChunkingStrategyFactory:
    """Factory for creating chunking strategies."""

    _strategies = {
        ChunkingStrategy.FIXED_SIZE: FixedSizeChunkingStrategy,
        ChunkingStrategy.SEMANTIC: SemanticChunkingStrategy,
        ChunkingStrategy.SENTENCE: SentenceChunkingStrategy,
        ChunkingStrategy.CODE: CodeChunkingStrategy,
        ChunkingStrategy.MARKDOWN: MarkdownChunkingStrategy,
        ChunkingStrategy.HTML: HTMLChunkingStrategy,
        ChunkingStrategy.HYBRID: HybridChunkingStrategy,
    }

    @classmethod
    def create_strategy(cls, config: ChunkingConfig) -> BaseChunkingStrategy:
        """Create a chunking strategy based on configuration.

        Args:
            config: Chunking configuration

        Returns:
            Configured chunking strategy instance

        Raises:
            ValueError: If strategy is not supported
        """
        if config.strategy not in cls._strategies:
            raise ValueError(f"Unsupported chunking strategy: {config.strategy}")

        strategy_class = cls._strategies[config.strategy]
        return strategy_class(config)

    @classmethod
    def get_available_strategies(cls) -> list[ChunkingStrategy]:
        """Get list of available chunking strategies."""
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_for_file_type(cls, file_extension: str) -> ChunkingStrategy:
        """Get recommended strategy for file type.

        Args:
            file_extension: File extension (e.g., '.pdf', '.md', '.py')

        Returns:
            Recommended chunking strategy
        """
        extension_strategies = {
            ".pdf": ChunkingStrategy.FIXED_SIZE,
            ".docx": ChunkingStrategy.FIXED_SIZE,
            ".txt": ChunkingStrategy.SENTENCE,
            ".md": ChunkingStrategy.MARKDOWN,
            ".html": ChunkingStrategy.HTML,
            ".htm": ChunkingStrategy.HTML,
            ".py": ChunkingStrategy.CODE,
            ".js": ChunkingStrategy.CODE,
            ".ts": ChunkingStrategy.CODE,
            ".java": ChunkingStrategy.CODE,
            ".cpp": ChunkingStrategy.CODE,
            ".c": ChunkingStrategy.CODE,
            ".cs": ChunkingStrategy.CODE,
            ".go": ChunkingStrategy.CODE,
            ".rs": ChunkingStrategy.CODE,
            ".php": ChunkingStrategy.CODE,
            ".rb": ChunkingStrategy.CODE,
        }

        return extension_strategies.get(file_extension.lower(), ChunkingStrategy.FIXED_SIZE)


def chunk_documents_with_strategy(
    documents: list[Document],
    config: ChunkingConfig,
    source_path: str | Path | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    **kwargs,
) -> list[BaseNode]:
    """Chunk documents using a specified strategy.

    Args:
        documents: List of documents to chunk
        config: Chunking configuration
        source_path: Optional source path for metadata
        progress_callback: Optional progress callback
        **kwargs: Additional strategy-specific parameters

    Returns:
        List of chunked nodes
    """
    logger.debug(
        "Chunking documents with strategy",
        strategy=config.strategy.value,
        num_documents=len(documents),
        chunk_size=config.chunk_size,
    )

    # Create strategy instance
    strategy = ChunkingStrategyFactory.create_strategy(config)

    # Chunk documents
    chunks = strategy.chunk_documents(documents, **kwargs)

    # Add metadata to chunks
    source_path = Path(source_path) if source_path else Path("unknown")
    for i, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "chunk_index": i,
                "document_name": source_path.name,
                "source": str(source_path),
                "chunking_strategy": strategy.get_strategy_name(),
                "chunk_size": len(chunk.text),
            }
        )

    logger.debug(
        "Chunking completed",
        strategy=strategy.get_strategy_name(),
        num_chunks=len(chunks),
        avg_chunk_size=sum(len(c.text) for c in chunks) / len(chunks) if chunks else 0,
    )

    return chunks


__all__ = [
    "ChunkingStrategy",
    "ChunkingConfig",
    "BaseChunkingStrategy",
    "FixedSizeChunkingStrategy",
    "SemanticChunkingStrategy",
    "SentenceChunkingStrategy",
    "CodeChunkingStrategy",
    "MarkdownChunkingStrategy",
    "HTMLChunkingStrategy",
    "HybridChunkingStrategy",
    "ChunkingStrategyFactory",
    "chunk_documents_with_strategy",
]
