"""
Local RAG (Retrieval-Augmented Generation) system implementation.

This module provides a complete RAG system that can:
- Load documents from various formats (PDF, DOCX, TXT, MD)
- Create and manage vector indices
- Query documents using local LLMs (Mistral via Ollama or HuggingFace)
- Provide source attribution for answers

The system is designed to run completely locally, using:
- LlamaIndex for document processing and retrieval
- HuggingFace embeddings for vector representations
- Mistral LLM (via Ollama or HuggingFace) for generation
"""

import os
from pathlib import Path
from typing import Any

import torch

# LlamaIndex imports
from llama_index.core import (
    Document,
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Alternative: Use Hugging Face Transformers for local Mistral
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.llms.ollama import Ollama
from llama_index.readers.file import DocxReader, PDFReader

# Local imports
from backend.rag_pipeline.config.parameter_sets import RAGParams
from backend.rag_pipeline.core.vector_store import VectorStoreManager, get_vector_store_manager_from_env
from backend.rag_pipeline.utils.directory_utils import (
    DirectoryEmptyError,
    ensure_directory,
    validate_directory,
)


class LocalRAGSystem:
    """
    A complete RAG system that runs locally using LlamaIndex and Mistral.

    This class provides a full implementation of a Retrieval-Augmented Generation
    system that can process documents, create vector indices, and answer questions
    using local LLMs and embeddings.

    Key features:
    - Document loading from multiple formats (PDF, DOCX, TXT, MD)
    - Local embedding generation using HuggingFace models
    - Local LLM inference using Ollama or HuggingFace
    - Source attribution and reference tracking
    - Persistent index storage and loading

    Example:
        >>> rag = LocalRAGSystem(input_data_dir="./my_data", index_storage_dir="./my_storage", embeddings_cache_dir="./my_cache")
        >>> documents = rag.load_mixed_documents() # Uses rag.input_data_dir by default
        >>> index = rag.create_index(documents) # Uses rag.index_storage_dir by default
        >>> result = rag.query(index, "What is the warranty period?")

    """

    def __init__(
        self,
        params: RAGParams,
        input_data_dir: str = "data",
        index_storage_dir: str = "storage",
        embeddings_cache_dir: str = "cache",
        vector_store_manager: VectorStoreManager | None = None,
    ):
        """
        Initialize the RAG system with specified configuration.

        Args:
            params: RAG parameters configuration
            input_data_dir: Directory for input documents.
            index_storage_dir: Directory for persistent index storage.
            embeddings_cache_dir: Directory for caching embeddings.
            vector_store_manager: Optional manager for vector store access. If
                not provided, it is created from environment variables.

        Raises:
            DirectoryError: If there are issues with directory creation or access.
            ValueError: If parameters are invalid.

        """
        # Validate parameters
        errors = params.validate()
        if errors:
            raise ValueError("Invalid parameters:\n" + "\n".join(f"- {e}" for e in errors))

        self.params = params

        # Ensure directories exist and are accessible
        self.input_data_dir = ensure_directory(
            input_data_dir,
            description="input data directory",
        )
        self.index_storage_dir = ensure_directory(
            index_storage_dir,
            description="index storage directory",
        )
        self.embeddings_cache_dir = ensure_directory(
            embeddings_cache_dir,
            description="embeddings cache directory",
        )

        self.vector_store_manager = vector_store_manager or get_vector_store_manager_from_env()

        # Initialize components and set global settings
        Settings.llm = self._setup_llm()
        Settings.embed_model = self._setup_embeddings()
        Settings.chunk_size = params.chunking.chunk_size
        Settings.chunk_overlap = params.chunking.chunk_overlap

        # Document readers for different file types
        self.pdf_reader = PDFReader()
        self.docx_reader = DocxReader()

    def _setup_llm(self):
        """
        Setup local LLM - using Ollama (recommended) or HuggingFace.

        Returns:
            An LLM instance configured for local inference.

        Note:
            First tries to use Ollama, falls back to HuggingFace if Ollama fails.
            For Ollama, ensure you have run: ollama pull mistral

        """
        # Option 1: Using Ollama (easier, recommended)
        try:
            llm = Ollama(
                model=self.params.llm.model_name,
                request_timeout=120.0,
                temperature=self.params.llm.temperature,
                system_prompt=(
                    "You are a helpful assistant that answers questions based on "
                    "the provided context. Always include specific references to "
                    "source documents and sections when possible. Format references "
                    "as {filename, section}: content. If the context doesn't contain "
                    "relevant information, say so clearly."
                ),
            )
            return llm
        except Exception as e:
            print(f"Ollama setup failed: {e}")
            print("Falling back to HuggingFace implementation...")
            return self._setup_hf_llm()

    def _setup_hf_llm(self):
        """
        Setup HuggingFace LLM for local inference.

        Returns:
            A HuggingFaceLLM instance configured for local inference.

        Note:
            Uses 8-bit quantization for memory efficiency.
            Requires sufficient GPU memory for inference.

        """
        model_name = os.getenv("HUGGINGFACE_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")

        # System prompt for RAG with source attribution
        system_message = (
            "You are a helpful assistant. Use the provided context to answer "
            "questions accurately. Always include specific references to source "
            "documents when possible using format {filename, section}: content. "
            "If the context doesn't contain relevant information, say so clearly."
        )

        # Query wrapper for Mistral format
        query_wrapper_prompt = f"<s>[INST] {system_message}\n\nContext: {{context_str}}\n\nQuestion: {{query_str}} [/INST]"

        llm = HuggingFaceLLM(
            model_name=model_name,
            tokenizer_name=model_name,
            query_wrapper_prompt=query_wrapper_prompt,
            context_window=4096,
            max_new_tokens=self.params.llm.max_tokens,
            model_kwargs={
                "torch_dtype": torch.float16,
                "load_in_8bit": True,  # For memory efficiency
            },
            tokenizer_kwargs={},
            generate_kwargs={
                "temperature": self.params.llm.temperature,
                "do_sample": True,
                "top_p": 0.9,
            },
            device_map="auto",
        )
        return llm

    def _setup_embeddings(self):
        """
        Setup local embedding model.

        Returns:
            A HuggingFaceEmbedding instance for generating text embeddings.

        """
        return HuggingFaceEmbedding(
            model_name=self.params.embedding.model_name,
            cache_folder=str(self.embeddings_cache_dir / "embeddings_cache"),
        )

    def load_pdf_documents(self, pdf_paths: list[str]) -> list[Document]:
        """
        Load multiple PDF documents with filename metadata.

        Args:
            pdf_paths: List of paths to PDF files to load.

        Returns:
            List of Document objects with metadata.

        Note:
            Each document includes metadata about its source file and page number.

        """
        documents = []

        for pdf_path_str in pdf_paths:
            pdf_path = Path(pdf_path_str)
            if not pdf_path.exists():
                print(f"Warning: PDF file {pdf_path} not found, skipping...")
                continue

            try:
                # Load PDF using PDFReader
                pdf_docs = self.pdf_reader.load_data(pdf_path)

                # Add filename metadata to each document
                filename = pdf_path.name
                for doc in pdf_docs:
                    doc.metadata["filename"] = filename
                    doc.metadata["source_type"] = "pdf"
                    # Add page number if available
                    if "page_label" in doc.metadata:
                        doc.metadata["reference"] = f"{filename}, page {doc.metadata['page_label']}"
                    else:
                        doc.metadata["reference"] = filename

                documents.extend(pdf_docs)
                print(f"Loaded PDF: {filename} ({len(pdf_docs)} pages)")

            except Exception as e:
                print(f"Error loading PDF {pdf_path}: {e}")

        return documents

    def load_docx_documents(self, docx_paths: list[str]) -> list[Document]:
        """
        Load multiple Word documents with filename metadata.

        Args:
            docx_paths: List of paths to DOCX files to load.

        Returns:
            List of Document objects with metadata.

        """
        documents = []

        for docx_path_str in docx_paths:
            docx_path = Path(docx_path_str)
            if not docx_path.exists():
                print(f"Warning: DOCX file {docx_path} not found, skipping...")
                continue

            try:
                # Load DOCX using DocxReader
                docx_docs = self.docx_reader.load_data(docx_path)

                # Add filename metadata
                filename = docx_path.name
                for doc in docx_docs:
                    doc.metadata["filename"] = filename
                    doc.metadata["source_type"] = "docx"
                    doc.metadata["reference"] = filename

                documents.extend(docx_docs)
                print(f"Loaded DOCX: {filename}")

            except Exception as e:
                print(f"Error loading DOCX {docx_path}: {e}")

        return documents

    def load_mixed_documents(self, data_path: str | None = None) -> list[Document]:
        """
        Load documents from directory - supports PDF, DOCX, TXT, MD.

        Args:
            data_path: Path to directory containing documents. Defaults to self.input_data_dir.

        Returns:
            List of Document objects with enhanced metadata.

        Raises:
            DirectoryError: If there are issues with the input directory.
            ValueError: If no supported documents are found.

        Note:
            Uses SimpleDirectoryReader to automatically handle multiple file types.
            Adds enhanced metadata for better source attribution.

        """
        resolved_data_path = Path(data_path) if data_path else self.input_data_dir

        # Validate input directory
        validate_directory(
            resolved_data_path,
            must_exist=True,
            must_be_readable=True,
            description="input data directory",
        )

        # Check if directory is empty
        if not any(resolved_data_path.iterdir()):
            raise DirectoryEmptyError(
                f"Input data directory is empty: {resolved_data_path}\n"
                f"Please add your documents (PDF, DOCX, TXT, MD) to this directory."
            )

        # SimpleDirectoryReader supports PDF, DOCX, TXT, MD, HTML, and more
        try:
            reader = SimpleDirectoryReader(
                input_dir=str(resolved_data_path),
                recursive=True,  # Search subdirectories
                required_exts=[".pdf", ".docx", ".txt", ".md"],  # Supported file types
            )

            documents = reader.load_data()

            if not documents:
                raise ValueError(
                    f"No supported documents found in: {resolved_data_path}\n"
                    f"Please add documents with these extensions: .pdf, .docx, .txt, .md"
                )

        except ValueError as e:
            if "No files found" in str(e):
                raise ValueError(
                    f"No supported documents found in: {resolved_data_path}\n"
                    f"Please add documents with these extensions: .pdf, .docx, .txt, .md"
                ) from e
            raise

        # Add enhanced metadata for better source attribution
        for doc in documents:
            if "file_path" in doc.metadata:
                filepath_str = doc.metadata["file_path"]
                filepath = Path(filepath_str)
                filename = filepath.name
                doc.metadata["filename"] = filename

                # Determine file type
                if filename.lower().endswith(".pdf"):
                    doc.metadata["source_type"] = "pdf"
                    # Add page info if available
                    if "page_label" in doc.metadata:
                        doc.metadata["reference"] = f"{filename}, page {doc.metadata['page_label']}"
                    else:
                        doc.metadata["reference"] = filename
                elif filename.lower().endswith(".docx"):
                    doc.metadata["source_type"] = "docx"
                    doc.metadata["reference"] = filename
                else:
                    doc.metadata["source_type"] = "text"
                    doc.metadata["reference"] = filename

        print(f"Loaded {len(documents)} document chunks from {resolved_data_path}")
        return documents

    def create_index(self, documents: list[Document], persist_dir: str | None = None):
        """
        Create vector index from documents with enhanced metadata.

        Args:
            documents: List of Document objects to index.
            persist_dir: Optional directory to save the index. Defaults to self.index_storage_dir.

        Returns:
            A VectorStoreIndex instance.

        Raises:
            DirectoryError: If there are issues with the index storage directory.

        Note:
            The index includes enhanced metadata for better source attribution
            and chunk relationships.

        """
        # Parse documents into nodes with metadata preservation
        node_parser = SimpleNodeParser.from_defaults(
            chunk_size=self.params.chunking.chunk_size,
            chunk_overlap=self.params.chunking.chunk_overlap,
            include_metadata=True,  # Preserve document metadata
            include_prev_next_rel=True,  # Track chunk relationships
        )

        nodes = node_parser.get_nodes_from_documents(documents)

        # Enhance node metadata for better source attribution
        for node in nodes:
            if hasattr(node, "metadata") and node.metadata:
                # Create a readable reference string
                if "reference" in node.metadata:
                    reference = node.metadata["reference"]
                else:
                    reference = node.metadata.get("filename", "Unknown source")

                # Add chunk identifier
                if hasattr(node, "node_id"):
                    node.metadata["chunk_id"] = node.node_id[:8]  # Short ID

                node.metadata["full_reference"] = reference

        # Create index using the configured vector store
        storage_context = self.vector_store_manager.get_storage_context()
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            show_progress=True,
        )

        # Persist index if path provided
        resolved_persist_dir = Path(persist_dir) if persist_dir else self.index_storage_dir
        if resolved_persist_dir:
            # Ensure directory exists and is writable
            validate_directory(
                resolved_persist_dir,
                must_exist=True,
                must_be_writable=True,
                create_if_missing=True,
                description="index storage directory",
            )
            index.storage_context.persist(str(resolved_persist_dir))
            print(f"Index saved to {resolved_persist_dir}")

        return index

    def load_index(self, persist_dir: str | None = None):
        """
        Load existing index from storage.

        Args:
            persist_dir: Directory containing the saved index. Defaults to self.index_storage_dir.

        Returns:
            A VectorStoreIndex instance loaded from storage.

        Raises:
            DirectoryError: If there are issues with the index directory.

        """
        resolved_persist_dir = Path(persist_dir) if persist_dir else self.index_storage_dir

        # Validate index directory
        validate_directory(
            resolved_persist_dir,
            must_exist=True,
            must_be_readable=True,
            description="index directory",
        )

        vs_context = self.vector_store_manager.get_storage_context()
        storage_context = StorageContext.from_defaults(
            persist_dir=str(resolved_persist_dir),
            vector_store=vs_context.vector_store,
        )
        index = load_index_from_storage(storage_context=storage_context)
        print(f"Index loaded from {resolved_persist_dir}")
        return index

    def query(
        self,
        index: VectorStoreIndex,
        question: str,
        include_sources: bool = True,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        """
        Query the RAG system with detailed source attribution.

        Args:
            index: VectorStoreIndex instance to query.
            question: Question to ask.
            include_sources: Whether to include source information in response.
            top_k: Optional override for number of chunks to retrieve.

        Returns:
            Dictionary containing:
            - answer: The generated answer
            - sources: List of source chunks used (if include_sources=True)

        Note:
            Each source includes:
            - rank: Position in retrieval results
            - score: Similarity score
            - reference: Source document reference
            - content_preview: Preview of source content
            - metadata: Full source metadata

        """
        query_engine = index.as_query_engine(
            similarity_top_k=top_k or self.params.retrieval.top_k,
            response_mode="compact",  # Better for source attribution
        )

        response = query_engine.query(question)

        result = {
            "answer": str(response),
            "sources": [],
        }

        # Extract source information
        if include_sources and hasattr(response, "source_nodes"):
            for i, node in enumerate(response.source_nodes):
                # Create clean, serializable metadata to avoid RelatedNodeInfo issues
                clean_metadata = {}
                if hasattr(node, "metadata") and node.metadata:
                    for key, value in node.metadata.items():
                        # Only include serializable types
                        if isinstance(value, str | int | float | bool | list | dict) and not key.startswith("_"):
                            if isinstance(value, list):
                                # Only include lists of basic types
                                if all(isinstance(item, str | int | float | bool) for item in value):
                                    clean_metadata[key] = value
                            elif isinstance(value, dict):
                                # Only include dicts with basic type values
                                if all(isinstance(v, str | int | float | bool | list) for v in value.values()):
                                    clean_metadata[key] = value
                            else:
                                clean_metadata[key] = value

                source_info = {
                    "rank": i + 1,
                    "score": getattr(node, "score", 0.0),
                    "reference": node.metadata.get("full_reference", "Unknown")
                    if hasattr(node, "metadata") and node.metadata
                    else "Unknown",
                    "content_preview": (node.text[:200] + "..." if len(node.text) > 200 else node.text),
                    "metadata": clean_metadata,
                }
                result["sources"].append(source_info)

        return result
