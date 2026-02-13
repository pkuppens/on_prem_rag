"""Performance tests for document ingestion pipeline.

As a user I want the ingestion pipeline to process large PDFs within acceptable time,
so that document upload remains responsive. Technical: 100-page PDF must load and chunk in < 60s.
"""

import tempfile
import time
from pathlib import Path

import pytest

from backend.rag_pipeline.core.chunking import chunk_documents
from backend.rag_pipeline.core.document_loader import DocumentLoader

# Stable URL for a 100+ page PDF (GPT-4 technical report, arXiv)
# PDF is fetched at test time; never stored in repo.
LARGE_PDF_URL = "https://arxiv.org/pdf/2303.08774.pdf"


@pytest.mark.internet
@pytest.mark.slow
class TestIngestionPerformance:
    """Performance tests for document ingestion."""

    def test_100_page_pdf_ingestion_under_60_seconds(self):
        """As a user I want 100+ page PDFs to ingest in < 60s, so upload stays responsive.

        Technical: Fetch PDF by reference (URL), load + chunk within 60 seconds.
        The PDF is not stored in the repo; it is downloaded at test time.
        """
        import httpx

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "large_doc.pdf"

            # Fetch by reference - PDF does not end up in repo
            with httpx.Client(follow_redirects=True, timeout=60) as client:
                response = client.get(LARGE_PDF_URL)
                response.raise_for_status()
                pdf_path.write_bytes(response.content)

            loader = DocumentLoader()
            start = time.perf_counter()

            documents, metadata = loader.load_document(pdf_path)
            chunking_result = chunk_documents(
                documents,
                source_path=pdf_path,
                chunk_size=512,
                chunk_overlap=50,
                enable_text_cleaning=True,
            )

            elapsed = time.perf_counter() - start

            assert metadata.num_pages >= 100, f"Expected 100+ pages, got {metadata.num_pages}"
            assert chunking_result.chunk_count > 0
            assert elapsed < 60, f"Ingestion took {elapsed:.1f}s, must complete in < 60s"
