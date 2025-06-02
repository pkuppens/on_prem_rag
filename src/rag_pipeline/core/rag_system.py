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
from typing import List, Optional, Dict, Any

# LlamaIndex imports
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    ServiceContext, 
    StorageContext,
    load_index_from_storage,
    Document
)
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.readers.file import PDFReader, DocxReader

# Alternative: Use Hugging Face Transformers for local Mistral
from llama_index.llms.huggingface import HuggingFaceLLM
import torch

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
DEFAULT_TEMPERATURE = 0.1      # Lower = more focused, higher = more creative
DEFAULT_MAX_TOKENS = 512       # Maximum response length


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
        >>> rag = LocalRAGSystem()
        >>> documents = rag.load_mixed_documents("./data")
        >>> index = rag.create_index(documents, persist_dir="./storage")
        >>> result = rag.query(index, "What is the warranty period?")
    """
    
    def __init__(self, 
                 model_name: str = DEFAULT_LLM_MODEL,
                 embed_model_name: str = DEFAULT_EMBED_MODEL,
                 chunk_size: int = DEFAULT_CHUNK_SIZE,
                 chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
                 top_k: int = DEFAULT_TOP_K):
        """
        Initialize the RAG system with specified configuration.
        
        Args:
            model_name: Name of the LLM model to use (default: "mistral")
            embed_model_name: Name of the embedding model
            chunk_size: Size of text chunks for processing (default: 512)
            chunk_overlap: Overlap between chunks (default: 50)
            top_k: Number of chunks to retrieve per query (default: 3)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embed_model_name = embed_model_name
        self.model_name = model_name
        self.top_k = top_k
        
        # Initialize components
        self.llm = self._setup_llm()
        self.embed_model = self._setup_embeddings()
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model=self.embed_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
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
                model=self.model_name,
                request_timeout=120.0,
                temperature=DEFAULT_TEMPERATURE,
                system_prompt=(
                    "You are a helpful assistant that answers questions based on "
                    "the provided context. Always include specific references to "
                    "source documents and sections when possible. Format references "
                    "as {filename, section}: content. If the context doesn't contain "
                    "relevant information, say so clearly."
                )
            )
            return llm
        except Exception as e:
            print(f"Ollama setup failed: {e}")
            print("Falling back to HuggingFace implementation...")
            
        # Option 2: Using HuggingFace Transformers directly
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
        model_name = "mistralai/Mistral-7B-Instruct-v0.2"
        
        # System prompt for RAG with source attribution
        system_message = (
            "You are a helpful assistant. Use the provided context to answer "
            "questions accurately. Always include specific references to source "
            "documents when possible using format {filename, section}: content. "
            "If the context doesn't contain relevant information, say so clearly."
        )
        
        # Query wrapper for Mistral format
        query_wrapper_prompt = (
            f"<s>[INST] {system_message}\n\n"
            "Context: {context_str}\n\n"
            "Question: {query_str} [/INST]"
        )
        
        llm = HuggingFaceLLM(
            model_name=model_name,
            tokenizer_name=model_name,
            query_wrapper_prompt=query_wrapper_prompt,
            context_window=4096,
            max_new_tokens=DEFAULT_MAX_TOKENS,
            model_kwargs={
                "torch_dtype": torch.float16,
                "load_in_8bit": True,  # For memory efficiency
            },
            tokenizer_kwargs={},
            generate_kwargs={
                "temperature": DEFAULT_TEMPERATURE,
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
            model_name=self.embed_model_name,
            cache_folder="./embeddings_cache"
        )
    
    def load_pdf_documents(self, pdf_paths: List[str]) -> List[Document]:
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
        
        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"Warning: PDF file {pdf_path} not found, skipping...")
                continue
                
            try:
                # Load PDF using PDFReader
                pdf_docs = self.pdf_reader.load_data(Path(pdf_path))
                
                # Add filename metadata to each document
                filename = os.path.basename(pdf_path)
                for doc in pdf_docs:
                    doc.metadata["filename"] = filename
                    doc.metadata["source_type"] = "pdf"
                    # Add page number if available
                    if "page_label" in doc.metadata:
                        doc.metadata["reference"] = (
                            f"{filename}, page {doc.metadata['page_label']}"
                        )
                    else:
                        doc.metadata["reference"] = filename
                
                documents.extend(pdf_docs)
                print(f"Loaded PDF: {filename} ({len(pdf_docs)} pages)")
                
            except Exception as e:
                print(f"Error loading PDF {pdf_path}: {e}")
                
        return documents
    
    def load_docx_documents(self, docx_paths: List[str]) -> List[Document]:
        """
        Load multiple Word documents with filename metadata.
        
        Args:
            docx_paths: List of paths to DOCX files to load.
            
        Returns:
            List of Document objects with metadata.
        """
        documents = []
        
        for docx_path in docx_paths:
            if not os.path.exists(docx_path):
                print(f"Warning: DOCX file {docx_path} not found, skipping...")
                continue
                
            try:
                # Load DOCX using DocxReader
                docx_docs = self.docx_reader.load_data(Path(docx_path))
                
                # Add filename metadata
                filename = os.path.basename(docx_path)
                for doc in docx_docs:
                    doc.metadata["filename"] = filename
                    doc.metadata["source_type"] = "docx"
                    doc.metadata["reference"] = filename
                
                documents.extend(docx_docs)
                print(f"Loaded DOCX: {filename}")
                
            except Exception as e:
                print(f"Error loading DOCX {docx_path}: {e}")
                
        return documents
    
    def load_mixed_documents(self, data_path: str) -> List[Document]:
        """
        Load documents from directory - supports PDF, DOCX, TXT, MD.
        
        Args:
            data_path: Path to directory containing documents.
            
        Returns:
            List of Document objects with enhanced metadata.
            
        Note:
            Uses SimpleDirectoryReader to automatically handle multiple file types.
            Adds enhanced metadata for better source attribution.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data path {data_path} not found")
        
        # SimpleDirectoryReader supports PDF, DOCX, TXT, MD, HTML, and more
        reader = SimpleDirectoryReader(
            input_dir=data_path,
            recursive=True,  # Search subdirectories
            required_exts=[".pdf", ".docx", ".txt", ".md"],  # Supported file types
        )
        
        documents = reader.load_data()
        
        # Add enhanced metadata for better source attribution
        for doc in documents:
            if "file_path" in doc.metadata:
                filepath = doc.metadata["file_path"]
                filename = os.path.basename(filepath)
                doc.metadata["filename"] = filename
                
                # Determine file type
                if filename.lower().endswith('.pdf'):
                    doc.metadata["source_type"] = "pdf"
                    # Add page info if available
                    if "page_label" in doc.metadata:
                        doc.metadata["reference"] = (
                            f"{filename}, page {doc.metadata['page_label']}"
                        )
                    else:
                        doc.metadata["reference"] = filename
                elif filename.lower().endswith('.docx'):
                    doc.metadata["source_type"] = "docx"
                    doc.metadata["reference"] = filename
                else:
                    doc.metadata["source_type"] = "text"
                    doc.metadata["reference"] = filename
        
        print(f"Loaded {len(documents)} document chunks from {data_path}")
        return documents
    
    def create_index(self, documents: List[Document], persist_dir: Optional[str] = None):
        """
        Create vector index from documents with enhanced metadata.
        
        Args:
            documents: List of Document objects to index.
            persist_dir: Optional directory to save the index.
            
        Returns:
            A VectorStoreIndex instance.
            
        Note:
            The index includes enhanced metadata for better source attribution
            and chunk relationships.
        """
        # Parse documents into nodes with metadata preservation
        node_parser = SimpleNodeParser.from_defaults(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            include_metadata=True,  # Preserve document metadata
            include_prev_next_rel=True  # Track chunk relationships
        )
        
        nodes = node_parser.get_nodes_from_documents(documents)
        
        # Enhance node metadata for better source attribution
        for node in nodes:
            if hasattr(node, 'metadata') and node.metadata:
                # Create a readable reference string
                if "reference" in node.metadata:
                    reference = node.metadata["reference"]
                else:
                    reference = node.metadata.get("filename", "Unknown source")
                
                # Add chunk identifier
                if hasattr(node, 'node_id'):
                    node.metadata["chunk_id"] = node.node_id[:8]  # Short ID
                    
                node.metadata["full_reference"] = reference
        
        # Create index
        index = VectorStoreIndex(
            nodes,
            service_context=self.service_context,
            show_progress=True
        )
        
        # Persist index if path provided
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
            index.storage_context.persist(persist_dir)
            print(f"Index saved to {persist_dir}")
            
        return index
    
    def load_index(self, persist_dir: str):
        """
        Load existing index from storage.
        
        Args:
            persist_dir: Directory containing the saved index.
            
        Returns:
            A VectorStoreIndex instance loaded from storage.
        """
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(
            storage_context,
            service_context=self.service_context
        )
        print(f"Index loaded from {persist_dir}")
        return index
    
    def query(self, index, question: str, include_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system with detailed source attribution.
        
        Args:
            index: VectorStoreIndex instance to query.
            question: Question to ask.
            include_sources: Whether to include source information in response.
            
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
            similarity_top_k=self.top_k,
            service_context=self.service_context,
            response_mode="compact"  # Better for source attribution
        )
        
        response = query_engine.query(question)
        
        result = {
            "answer": str(response),
            "sources": []
        }
        
        # Extract source information
        if include_sources and hasattr(response, 'source_nodes'):
            for i, node in enumerate(response.source_nodes):
                source_info = {
                    "rank": i + 1,
                    "score": getattr(node, 'score', 0.0),
                    "reference": node.metadata.get("full_reference", "Unknown"),
                    "content_preview": (
                        node.text[:200] + "..." if len(node.text) > 200 else node.text
                    ),
                    "metadata": dict(node.metadata)
                }
                result["sources"].append(source_info)
        
        return result 