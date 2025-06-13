# DOCX Processing

This document describes how DOCX files are processed in the RAG pipeline.

## Overview

DOCX files are processed similarly to PDFs, but with some key differences:

1. Text extraction is more reliable since DOCX is a native text format
2. The basic unit is paragraphs rather than pages
3. No previewer is available in the UI, only text display

## Text Extraction

The text extraction process:

1. Uses python-docx to read the document
2. Extracts text from each paragraph
3. Cleans the text by:
   - Removing special characters
   - Collapsing whitespace
   - Preserving paragraph structure

## UI Integration

The frontend handles DOCX files by:

1. Detecting file type from extension
2. Using DOCXViewer component for display
3. Showing text content in a scrollable container
4. Preserving paragraph formatting

## Code Structure

- `src/backend/rag_pipeline/utils/docx_utils.py`: Core extraction and cleaning functions
- `src/frontend/src/components/docx/DOCXViewer.tsx`: Frontend display component
- `tests/test_docx_utils.py`: Test cases for DOCX processing

## Usage Example

```python
from rag_pipeline.utils.docx_utils import extract_and_clean_docx

# Extract and clean text from a DOCX file
paragraphs = extract_and_clean_docx("path/to/document.docx")

# Each paragraph is a string in the list
for i, paragraph in enumerate(paragraphs):
    print(f"Paragraph {i + 1}: {paragraph}")
```

## Dependencies

- python-docx: For DOCX file reading
- llama-index: For document processing and chunking

## Testing

Run the DOCX processing tests with:

```bash
pytest tests/test_docx_utils.py
```

## Future Improvements

1. Add support for tables and other DOCX elements
2. Improve text cleaning for specific DOCX formatting
3. Add metadata extraction (author, creation date, etc.)
4. Consider adding a simple DOCX previewer in the UI

## References

- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [Chunking and Embedding](CHUNKING.md)

## Differences from PDF Processing

While similar to PDF processing, DOCX processing has some key differences:

1. DOCX files are structured documents with paragraphs, tables, and formatting
2. Text extraction is more reliable than PDFs since DOCX is a native text format
3. The cleaning process focuses on removing special characters and formatting artifacts
4. Paragraphs are used as the basic unit instead of pages

## UI Integration

For the UI integration, note that DOCX files do not have a previewer like PDFs. The frontend should:

1. Handle DOCX files gracefully by either:
   - Showing a placeholder message
   - Displaying the extracted text in a simple format
2. Not break when encountering DOCX files in search results
3. Clearly indicate the file type to users
