import pathlib

from rag_pipeline.config.parameter_sets import FAST_ANSWERS
from rag_pipeline.core.embeddings import process_pdf


def test_pdf_embedding_counts(test_case_dir):
    pdf_path = pathlib.Path("tests/test_data/2303.18223v16.pdf")
    persist = test_case_dir / "chroma"

    chunks, records = process_pdf(
        pdf_path,
        FAST_ANSWERS.embedding.model_name,
        persist_dir=str(persist),
        chunk_size=FAST_ANSWERS.chunking.chunk_size,
        chunk_overlap=FAST_ANSWERS.chunking.chunk_overlap,
        max_pages=1,
    )

    assert chunks == records
