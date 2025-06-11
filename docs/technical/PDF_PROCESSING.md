# PDF Processing

This document describes how PDFs are converted to plain text for the RAG pipeline.

Text extraction quality directly affects chunking and embedding. Utilities
introduced here allow manual inspection of conversion results and optional
cleanup of common artefacts such as hyphenated line breaks.

## Usage

```python
from rag_pipeline.utils.pdf_utils import extract_and_clean_pdf
pages = extract_and_clean_pdf("tests/test_data/2005.11401v4.pdf")
print(len(pages))
```

## References

- [PyPDF Documentation](https://pypdf.readthedocs.io/)
- [Chunking and Embedding](CHUNKING.md)

## Code Files

- [src/rag_pipeline/utils/pdf_utils.py](../../src/rag_pipeline/utils/pdf_utils.py) - Extraction and cleanup helpers
- [tests/test_pdf_utils.py](../../tests/test_pdf_utils.py) - Validation tests for PDF conversion
