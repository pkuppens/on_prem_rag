# Notebooks Documentation

This directory contains Jupyter notebooks that demonstrate and test various aspects of the RAG (Retrieval-Augmented Generation) pipeline. Each notebook serves a specific purpose in exploring, testing, or demonstrating functionality.

## Overview

The notebooks in this directory are designed to:

- Test core functionality of the RAG pipeline
- Demonstrate different parameter configurations
- Explore embedding and retrieval capabilities
- Debug and validate document processing
- Compare different approaches and configurations

## Notebooks

### 1. `pdf_conversion_debug.ipynb`

**Purpose**: Debug and validate PDF text extraction functionality

**What it does**:

- Tests PDF text extraction using the `extract_and_clean_pdf` function
- Validates that a specific test PDF (2005.11401v4.pdf) is processed correctly
- Ensures the extracted text contains exactly 19 pages
- Verifies that no explicit newlines are present in the extracted text
- Shows a preview of the first page content

**Key functionality tested**:

- PDF text extraction
- Page counting validation
- Text cleaning and formatting
- Error handling for malformed PDFs

**Usage**: Run this notebook to verify that PDF processing is working correctly before running other notebooks that depend on PDF processing.

### 2. `document_loader_example.ipynb`

**Purpose**: Demonstrate complete document loading and chunking workflow

**What it does**:

- Loads a PDF document using the RAG pipeline
- Applies page-based chunking with FAST_ANSWERS configuration parameters
- Demonstrates deduplication functionality
- Provides detailed reporting of chunking results
- Analyzes chunk distribution across pages

**Key functionality demonstrated**:

- Document loading with `process_pdf`
- Chunking with configurable parameters (chunk size, overlap)
- Deduplication to avoid redundant content processing
- Page-level analysis of chunk distribution
- Database persistence and retrieval

**Configuration used**: FAST_ANSWERS parameter set

- Chunk size: 512 tokens
- Chunk overlap: 50 tokens
- Model: sentence-transformers/all-MiniLM-L6-v2

**Usage**: Use this notebook to understand how documents are processed and chunked in the RAG pipeline.

### 3. `pdf_embedding.ipynb`

**Purpose**: Explore PDF embedding creation and querying with different parameter sets

**What it does**:

- Creates embeddings from PDF documents using different parameter configurations
- Processes multiple PDF files in the test data directory
- Demonstrates embedding storage and retrieval
- Tests similarity search functionality
- Compares similarity scores for related and unrelated queries

**Key functionality explored**:

- PDF chunking with `chunk_pdf`
- Embedding generation with `embed_chunks`
- Vector database storage and retrieval
- Similarity search with `query_embeddings`
- Parameter set comparison (fast, context_rich, precise)

**Configuration used**: "fast" parameter set by default

- Chunk size: 512 tokens
- Chunk overlap: 50 tokens
- Model: sentence-transformers/all-MiniLM-L6-v2

**Usage**: Use this notebook to understand how embeddings are created and how similarity search works.

### 4. `rag_exploration.ipynb`

**Purpose**: Explore the complete RAG system with LlamaIndex integration

**What it does**:

- Sets up a local RAG system using LlamaIndex
- Demonstrates document loading and indexing
- Shows query processing and response generation
- Tests multilingual queries (Dutch and English)
- Explores different types of questions and responses

**Key functionality explored**:

- LocalRAGSystem initialization
- Mixed document loading
- Index creation and management
- Query processing with context
- Multilingual support

**Configuration used**: FAST_ANSWERS parameter set

- Input data directory: `data/input_data`
- Index storage: `data/index_storage`
- Embeddings cache: `data/embeddings_cache`

**Usage**: Use this notebook to understand the complete RAG workflow and test different types of queries.

### 5. `top_k_comparison.ipynb`

**Purpose**: Compare retrieval performance for different top-k values

**What it does**:

- Tests semantic search with different top-k values (5, 10, 50)
- Measures retrieval performance and timing
- Validates consistency of top results across different k values
- Demonstrates that top-5 results remain consistent regardless of k

**Key functionality tested**:

- Top-k retrieval with different values
- Performance measurement
- Result consistency validation
- Similarity score comparison

**Configuration used**: "fast" parameter set

- Query: "Healthcare"
- Top-k values: 5, 10, 50

**Usage**: Use this notebook to understand how top-k retrieval works and validate that results are consistent.

## Setup and Dependencies

### Required Dependencies

All notebooks require the following dependencies to be installed:

- `llama-index` and related packages
- `sentence-transformers`
- `chromadb`
- `pypdf`
- `jupyter` and `nbconvert`

### Setup Script

Each notebook imports `setup_notebook.py` which:

- Adds the project's backend directory to the Python path
- Ensures proper module imports
- Provides environment setup for notebook execution

### Running Notebooks

To run the notebooks:

1. **Using uv (recommended)**:

   ```bash
   cd notebooks
   uv run jupyter notebook
   ```

2. **Using Python directly**:

   ```bash
   cd notebooks
   uv run python -c "import setup_notebook; exec(open('notebook_name.ipynb').read())"
   ```

3. **Using nbconvert**:
   ```bash
   cd notebooks
   uv run jupyter nbconvert --to notebook --execute notebook_name.ipynb
   ```

## Test Data

The notebooks use test data from the `tests/test_data/` directory:

- `2005.11401v4.pdf` - Used for PDF conversion debugging
- `2303.18223v16.pdf` - Used for embedding and retrieval testing

## Configuration Parameters

The notebooks use different parameter sets defined in `rag_pipeline.config.parameter_sets`:

### FAST_ANSWERS

- Chunk size: 512 tokens
- Chunk overlap: 50 tokens
- Model: sentence-transformers/all-MiniLM-L6-v2
- Use case: Quick responses, general purpose

### PRECISE_ANSWERS

- Chunk size: 1024 tokens
- Chunk overlap: 100 tokens
- Model: sentence-transformers/all-MiniLM-L6-v2
- Use case: Detailed analysis, comprehensive responses

### CONTEXT_RICH

- Chunk size: 2048 tokens
- Chunk overlap: 200 tokens
- Model: sentence-transformers/all-MiniLM-L6-v2
- Use case: Context-heavy documents, detailed analysis

## Output and Results

### Data Storage

- Embeddings are stored in `data/` subdirectories
- Each parameter set creates its own storage directory
- ChromaDB is used for vector storage
- SQLite databases store metadata and embeddings

### Performance Metrics

The notebooks provide various performance metrics:

- Processing time for document chunking
- Embedding generation time
- Query response time
- Similarity scores and rankings
- Deduplication ratios

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `setup_notebook.py` is imported first
2. **Path Issues**: Run notebooks from the `notebooks/` directory
3. **Missing Dependencies**: Use `uv sync --dev` to install all dependencies
4. **Memory Issues**: Large documents may require significant memory
5. **Timeout Issues**: Some operations may take time for large documents

### Debugging Tips

1. Start with `pdf_conversion_debug.ipynb` to verify basic functionality
2. Use smaller test documents for initial testing
3. Check the `data/` directory for existing embeddings to avoid reprocessing
4. Monitor memory usage during embedding generation
5. Use the test scripts in the notebooks directory for automated testing

## Integration with Main Project

These notebooks are designed to:

- Test functionality before integration into the main application
- Demonstrate usage patterns for the RAG pipeline
- Validate parameter configurations
- Debug issues in document processing
- Explore new features and configurations

The notebooks use the same codebase as the main application, ensuring consistency between testing and production use.

## Future Enhancements

Potential improvements for the notebooks:

- Automated testing suite for all notebooks
- Performance benchmarking across different configurations
- Integration with CI/CD pipeline
- Additional test documents and scenarios
- Visualization of embedding spaces and similarity distributions
- Comparative analysis of different embedding models
