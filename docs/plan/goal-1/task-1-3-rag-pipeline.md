# Task 1.3: RAG Pipeline MVP Implementation

## Context from Goal 1

This task implements the core RAG pipeline that enables document ingestion, vectorization, and question-answering capabilities. This forms the foundation of our on-premises solution, demonstrating the business value while establishing the technical architecture for all future enhancements.

## Problem Statement

We need a functional RAG pipeline that:
- Ingests and processes various document formats (PDF, DOCX, TXT)
- Converts documents to meaningful vector embeddings
- Stores embeddings in a local vector database
- Retrieves relevant context for user queries
- Generates accurate answers using local LLMs

## Technology Considerations

### Document Loading Options

#### Option 1: LangChain Loaders (Chosen)
- **Pros**: Mature ecosystem, handles multiple formats, chunking strategies
- **Cons**: Large dependency, some overhead
- **Use Case**: Production applications needing robust document processing

#### Option 2: Custom Loaders
- **Pros**: Lightweight, full control, minimal dependencies
- **Cons**: Significant development effort, need to handle edge cases
- **Use Case**: Specialized requirements, minimal overhead needed

#### Option 3: Unstructured.io
- **Pros**: Advanced document parsing, excellent format support
- **Cons**: Additional dependency, cloud-based features
- **Use Case**: Complex document structures, advanced parsing needs

### Embedding Model Options

#### Option 1: Sentence-Transformers (Chosen)
- **Pros**: Local execution, good performance, multilingual support
- **Cons**: Larger model sizes, resource intensive
- **Use Case**: Quality over speed, offline requirements

#### Option 2: OpenAI Embeddings
- **Pros**: Excellent quality, maintained by OpenAI
- **Cons**: Cloud dependency, cost per request
- **Use Case**: Cloud-hybrid deployments

#### Option 3: Hugging Face Transformers
- **Pros**: Latest models, extensive options
- **Cons**: Complex setup, model compatibility issues
- **Use Case**: Research, cutting-edge model requirements

### Decision: LangChain + Sentence-Transformers + ChromaDB

**Rationale**: Balanced approach prioritizing reliability and offline capability while maintaining good performance and developer experience.

## Implementation Steps

### Step 1: Create Document Ingestion Module

Create `src/rag_system/ingestion/document_loader.py`:

```python
"""Document ingestion and processing module."""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

from langchain.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Supported document types."""
    
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"


class DocumentProcessor:
    """Handles document loading and processing."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunk_size: int = 4000,
    ):
        """Initialize document processor.
        
        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between chunks
            max_chunk_size: Maximum allowed chunk size
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_chunk_size = max_chunk_size
        
        # Configure text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        # Loader mapping
        self.loaders = {
            DocumentType.PDF: PyPDFLoader,
            DocumentType.DOCX: Docx2txtLoader,
            DocumentType.TXT: TextLoader,
            DocumentType.MD: UnstructuredMarkdownLoader,
        }

    def load_documents(self, directory: Path) -> List[Document]:
        """Load all supported documents from directory.
        
        Args:
            directory: Path to directory containing documents
            
        Returns:
            List of loaded documents
        """
        documents = []
        
        for doc_type in DocumentType:
            pattern = f"**/*.{doc_type.value}"
            try:
                loader = DirectoryLoader(
                    str(directory),
                    glob=pattern,
                    loader_cls=self.loaders[doc_type],
                    loader_kwargs=self._get_loader_kwargs(doc_type),
                )
                docs = loader.load()
                logger.info(f"Loaded {len(docs)} {doc_type.value} documents")
                documents.extend(docs)
            except Exception as e:
                logger.warning(f"Failed to load {doc_type.value} documents: {e}")
        
        return documents

    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process documents by chunking and adding metadata.
        
        Args:
            documents: List of raw documents
            
        Returns:
            List of processed document chunks
        """
        processed_docs = []
        
        for doc in documents:
            # Validate document
            if not self._validate_document(doc):
                continue
                
            # Split document into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Enhance metadata for each chunk
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_id": f"{doc.metadata.get('source', 'unknown')}_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk.page_content),
                    "processing_timestamp": self._get_timestamp(),
                })
                processed_docs.append(chunk)
        
        logger.info(f"Processed {len(processed_docs)} document chunks")
        return processed_docs

    def _validate_document(self, doc: Document) -> bool:
        """Validate document content and metadata."""
        if not doc.page_content.strip():
            logger.warning(f"Empty document: {doc.metadata.get('source')}")
            return False
            
        if len(doc.page_content) > self.max_chunk_size * 100:
            logger.warning(f"Document too large: {doc.metadata.get('source')}")
            return False
            
        return True

    def _get_loader_kwargs(self, doc_type: DocumentType) -> Dict[str, Any]:
        """Get loader-specific keyword arguments."""
        kwargs = {}
        
        if doc_type == DocumentType.TXT:
            kwargs["encoding"] = "utf-8"
        elif doc_type == DocumentType.PDF:
            kwargs["extract_images"] = False
            
        return kwargs

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
```

### Step 2: Create Vector Store Manager

Create `src/rag_system/storage/vector_store.py`:

```python
"""Vector store management using ChromaDB."""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages vector storage and retrieval operations."""
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = "./data/vectordb",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """Initialize vector store manager.
        
        Args:
            collection_name: Name of the vector collection
            persist_directory: Directory to persist vector data
            embedding_model: Sentence transformer model name
        """
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=embedding_model
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to vector store.
        
        Args:
            documents: List of documents to add
            
        Returns:
            List of document IDs
        """
        if not documents:
            logger.warning("No documents to add")
            return []
        
        try:
            # Generate unique IDs for documents
            ids = [
                f"{doc.metadata.get('chunk_id', f'doc_{i}')}"
                for i, doc in enumerate(documents)
            ]
            
            # Add documents to vector store
            self.vector_store.add_documents(documents=documents, ids=ids)
            
            logger.info(f"Added {len(documents)} documents to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar documents
        """
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_metadata,
            )
            
            logger.debug(f"Found {len(results)} similar documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        score_threshold: float = 0.0,
    ) -> List[tuple[Document, float]]:
        """Search with similarity scores.
        
        Args:
            query: Search query
            k: Number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of (document, score) tuples
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query, k=k
            )
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= score_threshold
            ]
            
            logger.debug(f"Found {len(filtered_results)} documents above threshold")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similarity search with score failed: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection."""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "name": collection.name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}

    def delete_collection(self) -> bool:
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
```

### Step 3: Create RAG Query Engine

Create `src/rag_system/retrieval/qa_engine.py`:

```python
"""Question-answering engine using RAG."""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from ..storage.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


@dataclass
class QAResult:
    """Result from QA query."""
    
    answer: str
    source_documents: List[Document]
    confidence: float
    query_time: float
    metadata: Dict[str, Any]


class RAGQueryEngine:
    """RAG-based question answering engine."""
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        ollama_url: str = "http://localhost:11434",
        model_name: str = "llama3",
        temperature: float = 0.1,
    ):
        """Initialize QA engine.
        
        Args:
            vector_store_manager: Vector store for document retrieval
            ollama_url: Ollama server URL
            model_name: LLM model name
            temperature: LLM temperature setting
        """
        self.vector_store_manager = vector_store_manager
        
        # Initialize LLM
        self.llm = Ollama(
            base_url=ollama_url,
            model=model_name,
            temperature=temperature,
        )
        
        # Create custom prompt template
        self.prompt_template = PromptTemplate(
            template=self._get_prompt_template(),
            input_variables=["context", "question"]
        )
        
        # Initialize retrieval chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store_manager.vector_store.as_retriever(
                search_kwargs={"k": 4}
            ),
            chain_type_kwargs={
                "prompt": self.prompt_template
            },
            return_source_documents=True,
        )

    def query(self, question: str, **kwargs) -> QAResult:
        """Process a question and return answer with sources.
        
        Args:
            question: User question
            **kwargs: Additional parameters
            
        Returns:
            QA result with answer and metadata
        """
        import time
        
        start_time = time.time()
        
        try:
            # Execute query
            result = self.qa_chain({
                "query": question,
                **kwargs
            })
            
            query_time = time.time() - start_time
            
            # Calculate confidence based on source relevance
            confidence = self._calculate_confidence(
                question, result.get("source_documents", [])
            )
            
            return QAResult(
                answer=result["result"],
                source_documents=result.get("source_documents", []),
                confidence=confidence,
                query_time=query_time,
                metadata={
                    "model": self.llm.model,
                    "question_length": len(question),
                    "source_count": len(result.get("source_documents", [])),
                }
            )
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QAResult(
                answer=f"I apologize, but I encountered an error: {str(e)}",
                source_documents=[],
                confidence=0.0,
                query_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def _get_prompt_template(self) -> str:
        """Get the prompt template for QA."""
        return """You are a helpful assistant that answers questions based on the provided context.

Use the following pieces of context to answer the question at the end. If you don't know the answer based on the context, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}

Instructions:
1. Base your answer only on the provided context
2. Be concise and accurate
3. If the context doesn't contain enough information, say so
4. Include relevant details from the context when helpful

Answer:"""

    def _calculate_confidence(
        self, question: str, source_documents: List[Document]
    ) -> float:
        """Calculate confidence score for the answer."""
        if not source_documents:
            return 0.0
        
        # Simple confidence calculation based on:
        # - Number of source documents
        # - Average chunk size
        # - Question-context overlap
        
        doc_count_score = min(len(source_documents) / 4.0, 1.0)
        
        avg_chunk_size = sum(
            len(doc.page_content) for doc in source_documents
        ) / len(source_documents)
        size_score = min(avg_chunk_size / 1000.0, 1.0)
        
        # Simple keyword overlap
        question_words = set(question.lower().split())
        context_words = set()
        for doc in source_documents:
            context_words.update(doc.page_content.lower().split())
        
        overlap = len(question_words.intersection(context_words))
        overlap_score = min(overlap / len(question_words), 1.0)
        
        # Weighted average
        confidence = (
            0.4 * doc_count_score +
            0.3 * size_score +
            0.3 * overlap_score
        )
        
        return round(confidence, 2)

    def update_retriever_config(self, **kwargs) -> None:
        """Update retriever configuration."""
        self.qa_chain.retriever = self.vector_store_manager.vector_store.as_retriever(
            search_kwargs=kwargs
        )
        logger.info(f"Updated retriever config: {kwargs}")
```

### Step 4: Create Integration Module

Create `src/rag_system/rag_system.py`:

```python
"""Main RAG system integration."""

import logging
from pathlib import Path
from typing import List, Optional

from .ingestion.document_loader import DocumentProcessor
from .storage.vector_store import VectorStoreManager
from .retrieval.qa_engine import RAGQueryEngine, QAResult

logger = logging.getLogger(__name__)


class RAGSystem:
    """Main RAG system orchestrator."""
    
    def __init__(
        self,
        data_directory: str = "./data",
        collection_name: str = "documents",
        model_name: str = "llama3",
        ollama_url: str = "http://localhost:11434",
    ):
        """Initialize RAG system.
        
        Args:
            data_directory: Base data directory
            collection_name: Vector collection name
            model_name: LLM model name
            ollama_url: Ollama server URL
        """
        self.data_directory = Path(data_directory)
        self.documents_directory = self.data_directory / "documents"
        self.documents_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.vector_store_manager = VectorStoreManager(
            collection_name=collection_name,
            persist_directory=str(self.data_directory / "vectordb"),
        )
        self.qa_engine = RAGQueryEngine(
            vector_store_manager=self.vector_store_manager,
            ollama_url=ollama_url,
            model_name=model_name,
        )

    def ingest_documents(self, directory: Optional[Path] = None) -> int:
        """Ingest documents from directory.
        
        Args:
            directory: Directory containing documents (default: self.documents_directory)
            
        Returns:
            Number of document chunks ingested
        """
        if directory is None:
            directory = self.documents_directory
        
        logger.info(f"Starting document ingestion from: {directory}")
        
        # Load and process documents
        documents = self.document_processor.load_documents(directory)
        if not documents:
            logger.warning("No documents found to ingest")
            return 0
        
        processed_docs = self.document_processor.process_documents(documents)
        
        # Add to vector store
        self.vector_store_manager.add_documents(processed_docs)
        
        logger.info(f"Successfully ingested {len(processed_docs)} document chunks")
        return len(processed_docs)

    def query(self, question: str) -> QAResult:
        """Query the RAG system.
        
        Args:
            question: User question
            
        Returns:
            QA result with answer and sources
        """
        logger.info(f"Processing query: {question[:50]}...")
        return self.qa_engine.query(question)

    def get_system_status(self) -> dict:
        """Get system status information."""
        collection_info = self.vector_store_manager.get_collection_info()
        
        return {
            "documents_directory": str(self.documents_directory),
            "collection_info": collection_info,
            "model": self.qa_engine.llm.model,
            "status": "ready" if collection_info.get("count", 0) > 0 else "no_documents"
        }
```

## Testing and Validation

### Step 5: Create Test Suite

Create `tests/test_rag_pipeline.py`:

```python
"""Test suite for RAG pipeline."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.rag_system.rag_system import RAGSystem


@pytest.fixture
def temp_documents():
    """Create temporary documents for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create test documents
    (temp_dir / "test1.txt").write_text("This is a test document about artificial intelligence.")
    (temp_dir / "test2.txt").write_text("Machine learning is a subset of artificial intelligence.")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_document_ingestion(temp_documents):
    """Test document ingestion."""
    rag_system = RAGSystem()
    
    # Ingest test documents
    count = rag_system.ingest_documents(temp_documents)
    
    assert count > 0
    
    # Check system status
    status = rag_system.get_system_status()
    assert status["status"] == "ready"


def test_query_processing(temp_documents):
    """Test query processing."""
    rag_system = RAGSystem()
    
    # Ingest documents first
    rag_system.ingest_documents(temp_documents)
    
    # Test query
    result = rag_system.query("What is artificial intelligence?")
    
    assert result.answer
    assert len(result.source_documents) > 0
    assert result.confidence > 0
```

## Definition of Done

### Core Functionality
- [ ] Document ingestion working for PDF, DOCX, TXT files
- [ ] Vector embeddings generated and stored
- [ ] Q&A queries returning relevant answers
- [ ] Source document attribution working
- [ ] Confidence scoring implemented

### Performance
- [ ] Document processing under 10 seconds for typical files
- [ ] Query response time under 5 seconds
- [ ] Memory usage optimized for target hardware

### Code Quality
- [ ] Unit tests passing
- [ ] Integration tests working
- [ ] Error handling implemented
- [ ] Logging properly configured

### Documentation
- [ ] API documentation complete
- [ ] Usage examples provided
- [ ] Troubleshooting guide created

## Common Issues and Solutions

### Issue 1: Ollama Connection Failed
**Solution**: Ensure Ollama is running and accessible
```bash
curl http://localhost:11434/api/version
```

### Issue 2: ChromaDB Permissions
**Solution**: Fix directory permissions
```bash
chmod -R 755 ./data/vectordb
```

### Issue 3: Out of Memory During Embedding
**Solution**: Process documents in smaller batches or reduce chunk size

## Next Steps

1. Proceed to [Goal 2: Documentation Excellence](../goal-2.md)
2. Implement monitoring and metrics collection
3. Optimize performance based on initial testing

## References

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama Documentation](https://ollama.ai/docs/) 