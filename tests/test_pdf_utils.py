import pytest

from rag_pipeline.utils.pdf_utils import clean_pdf_text, extract_pdf_text


@pytest.mark.skipif(not pytest.importorskip("pypdf", reason="pypdf not installed"), reason="pypdf missing")
def test_extract_pdf_text(test_data_dir):
    pdf_path = test_data_dir / "2005.11401v4.pdf"
    pages = extract_pdf_text(pdf_path)
    assert isinstance(pages, list)
    assert pages
    assert all(isinstance(p, str) for p in pages)


def test_clean_pdf_text():
    raw = "Example hy-\nphenated word."
    cleaned = clean_pdf_text(raw)
    assert "hyphenated" in cleaned
    assert "\n" not in cleaned
