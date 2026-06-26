"""Document loader infrastructure — file-to-text readers.

This module adapts LlamaIndex file readers to produce domain
``IngestionDocument`` objects. The LlamaIndex dependency is isolated here;
other ingestion modules work with domain types only.

Supported formats: PDF, DOCX, MD, TXT, HTML
"""

from __future__ import annotations

import hashlib
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from backend.ingestion.domain.value_objects import IngestionDocument

# Lazy LlamaIndex imports — allow tests to run without optional deps
Document = object
SimpleDirectoryReader = object
DocxReader = MarkdownReader = PDFReader = None

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Template interface for document processors."""

    @abstractmethod
    def load(self, file_path: Path) -> list[IngestionDocument]:
        """Return IngestionDocument objects for the given file."""


class PDFProcessor(BaseProcessor):
    def __init__(self) -> None:
        global PDFReader
        from llama_index.readers.file import PDFReader

        self._reader = PDFReader()

    def load(self, file_path: Path) -> list[IngestionDocument]:
        raw_docs = self._reader.load_data(file_path)
        return [_convert_llama_document(d) for d in raw_docs]


class DocxProcessor(BaseProcessor):
    def __init__(self) -> None:
        global DocxReader
        from llama_index.readers.file import DocxReader

        self._reader = DocxReader()

    def load(self, file_path: Path) -> list[IngestionDocument]:
        raw_docs = self._reader.load_data(file_path)
        return [_convert_llama_document(d) for d in raw_docs]


class MarkdownProcessor(BaseProcessor):
    def __init__(self) -> None:
        global MarkdownReader
        from llama_index.readers.file import MarkdownReader

        self._reader = MarkdownReader()

    def load(self, file_path: Path) -> list[IngestionDocument]:
        raw_docs = self._reader.load_data(file_path)
        return [_convert_llama_document(d) for d in raw_docs]


class TextProcessor(BaseProcessor):
    def __init__(self) -> None:
        global SimpleDirectoryReader
        from llama_index.core import SimpleDirectoryReader

        self._reader_cls = SimpleDirectoryReader

    def load(self, file_path: Path) -> list[IngestionDocument]:
        reader = self._reader_cls(input_files=[str(file_path)])
        raw_docs = reader.load_data(str(file_path))
        return [_convert_llama_document(d) for d in raw_docs]


class _HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML, stripping tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)

    def get_text(self) -> str:
        return "".join(self.text_parts)


class _HTMLHeadingExtractor(HTMLParser):
    """Extract section headings (h1-h6) from HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.headings: list[str] = []
        self._in_heading = False
        self._current_heading: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = True
            self._current_heading = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self._current_heading:
                self.headings.append(" ".join(self._current_heading).strip())
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._current_heading.append(data)


class HtmlProcessor(BaseProcessor):
    """Load HTML files and extract text content for RAG ingestion."""

    def load(self, file_path: Path) -> list[IngestionDocument]:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        extractor = _HTMLTextExtractor()
        extractor.feed(content)
        text = extractor.get_text().strip()
        if not text:
            text = "(No text content extracted from HTML)"
        return [IngestionDocument(text=text, metadata={"file_path": str(file_path)})]


def _convert_llama_document(li_doc: object) -> IngestionDocument:
    """Convert a LlamaIndex ``Document`` to a domain ``IngestionDocument``.

    Args:
        li_doc: A ``llama_index.core.Document`` instance.

    Returns:
        ``IngestionDocument`` with text and serializable metadata.
    """
    text = getattr(li_doc, "text", "") or ""
    metadata = {}
    raw_meta = getattr(li_doc, "metadata", None) or {}
    for k, v in raw_meta.items():
        if isinstance(v, str | int | float | bool):
            metadata[k] = v
    return IngestionDocument(text=str(text), metadata=metadata)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt", ".html", ".htm"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


class DocumentLoader:
    """Loads files into domain ``IngestionDocument`` objects.

    Delegates to format-specific processors that internally use LlamaIndex
    readers. The LlamaIndex ``Document`` type is converted to the domain
    ``IngestionDocument`` type before being returned.
    """

    def __init__(self) -> None:
        self.processed_files: set[tuple[str, str]] = set()
        self._setup_processors()

    def _setup_processors(self) -> None:
        self.processors: dict[str, BaseProcessor] = {
            ".pdf": PDFProcessor(),
            ".docx": DocxProcessor(),
            ".md": MarkdownProcessor(),
            ".txt": TextProcessor(),
            ".html": HtmlProcessor(),
            ".htm": HtmlProcessor(),
        }

    def _compute_file_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _validate_file(self, file_path: Path) -> tuple[bool, str | None]:
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format: {file_path.suffix}"
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False, f"File too large: {file_path.stat().st_size} bytes"
        return True, None

    def _get_metadata(self, file_path: Path, file_hash: str) -> dict:
        return {
            "file_path": str(file_path),
            "file_hash": file_hash,
            "file_type": file_path.suffix.lower(),
            "file_size": file_path.stat().st_size,
        }

    def _extract_creation_date(self, file_path: Path) -> str | None:
        try:
            if file_path.suffix.lower() == ".pdf":
                try:
                    from pypdf import PdfReader

                    reader = PdfReader(file_path)
                    if reader.metadata and reader.metadata.get("/CreationDate"):
                        raw = str(reader.metadata.get("/CreationDate", ""))
                        if raw.startswith("D:"):
                            raw = raw[2:]
                        if len(raw) >= 8:
                            return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
                except Exception:  # noqa: S110
                    pass
            mtime = file_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
        except Exception:  # noqa: S110
            return None

    def _extract_section_headings(self, file_path: Path, file_type: str) -> list[str]:
        headings: list[str] = []
        try:
            if file_type in (".md", ".markdown"):
                content = file_path.read_text(encoding="utf-8", errors="replace")
                for match in re.finditer(r"^#{1,6}\s+(.+)$", content, re.MULTILINE):
                    headings.append(match.group(1).strip())
            elif file_type in (".html", ".htm"):
                content = file_path.read_text(encoding="utf-8", errors="replace")
                extractor = _HTMLHeadingExtractor()
                extractor.feed(content)
                headings = extractor.headings
        except Exception:  # noqa: S110
            pass
        return headings

    def load_document(
        self,
        file_path: str | Path,
        *,
        params_key: str = "default",
    ) -> tuple[list[IngestionDocument], dict]:
        """Load a document and return domain documents with metadata.

        Args:
            file_path: Path to the document file.
            params_key: Identifier for the parameter set used.

        Returns:
            Tuple of (list of IngestionDocument, metadata dict).

        Raises:
            ValueError: If file validation fails.
            OSError: If file processing fails.
        """
        file_path = Path(file_path)

        is_valid, error_msg = self._validate_file(file_path)
        if not is_valid:
            raise ValueError(error_msg)

        file_hash = self._compute_file_hash(file_path)
        dedup_key = (file_hash, params_key)
        if dedup_key in self.processed_files:
            logger.debug(f"Skipping duplicate file: {file_path} ({params_key})")
            return [], self._get_metadata(file_path, file_hash)

        try:
            processor = self.processors[file_path.suffix.lower()]
            documents = processor.load(file_path)

            metadata = self._get_metadata(file_path, file_hash)
            if file_path.suffix.lower() == ".pdf":
                metadata["num_pages"] = len(documents)
            elif file_path.suffix.lower() == ".docx":
                metadata["num_pages"] = len(documents)

            creation_date = self._extract_creation_date(file_path)
            if creation_date:
                metadata["creation_date"] = creation_date

            headings = self._extract_section_headings(file_path, file_path.suffix.lower())
            if headings:
                metadata["section_headings"] = headings

            self.processed_files.add(dedup_key)

            logger.info(f"Successfully loaded document: {file_path}")
            return documents, metadata

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            metadata = self._get_metadata(file_path, file_hash)
            metadata["processing_status"] = "error"
            metadata["error_message"] = error_msg
            raise OSError(error_msg) from e
