#!/usr/bin/env python3
"""Fetch clinical guideline PDFs by reference.

Downloads NHG-Standaarden and other public guidelines to a local directory
for ingestion into the RAG pipeline. Idempotent: skips files that already exist.
See docs/portfolio/HEALTHCARE_GUIDELINES_SOURCES.md for the full source list.

Created: 2026-02-21
Updated: 2026-02-21
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("tmp/healthcare_guidelines")


@dataclass(frozen=True)
class FetchResult:
    """Result of a fetch run.

    Attributes:
        output_dir: Directory where PDFs are stored.
        downloaded: Filenames of newly downloaded files.
        skipped: Count of sources skipped (file already existed).
        skipped_files: Filenames that were skipped (already present).
    """

    output_dir: Path
    downloaded: tuple[str, ...]
    skipped: int
    skipped_files: tuple[str, ...]


@dataclass(frozen=True)
class GuidelineSource:
    """A clinical guideline PDF source.

    Attributes:
        url: Direct URL to the PDF.
        title: Human-readable title (e.g. "Urineweginfecties").
        filename: Output filename (e.g. "Urineweginfecties.pdf").
    """

    url: str
    title: str
    filename: str


# NHG-Standaarden: Dutch drug-prescription guidelines. PDFs at richtlijnen.nhg.org.
DEFAULT_NHG_SOURCES: list[GuidelineSource] = [
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/9428_Urineweginfecties_december-2025.pdf",
        title="Urineweginfecties",
        filename="NHG_Urineweginfecties.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/3202_Fluor%20vaginalis_januari-2024.pdf",
        title="Fluor vaginalis",
        filename="NHG_Fluor_vaginalis.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/6020_Depressie_januari-2024.pdf",
        title="Depressie",
        filename="NHG_Depressie.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/3509_Angst_september-2025.pdf",
        title="Angst",
        filename="NHG_Angst.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/6215_Slaapproblemen_januari-2026.pdf",
        title="Slaapproblemen",
        filename="NHG_Slaapproblemen.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/10271_Maagklachten_april-2025.pdf",
        title="Maagklachten",
        filename="NHG_Maagklachten.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/4201_Acute%20diarree_mei-2024.pdf",
        title="Acute diarree",
        filename="NHG_Acute_diarree.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/6101_Obstipatie%20_september-2010.pdf",
        title="Obstipatie",
        filename="NHG_Obstipatie.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/7880_Acuut%20hoesten_juli-2025.pdf",
        title="Acuut hoesten",
        filename="NHG_Acuut_hoesten.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/4254_Acute%20rhinosinusitis_mei-2024.pdf",
        title="Acute rhinosinusitis",
        filename="NHG_Acute_rhinosinusitis.pdf",
    ),
    GuidelineSource(
        url="https://richtlijnen.nhg.org/files/pdf/5806_Acute%20keelpijn_augustus-2015.pdf",
        title="Acute keelpijn",
        filename="NHG_Acute_keelpijn.pdf",
    ),
]


def fetch_healthcare_guidelines(
    sources: list[GuidelineSource],
    output_dir: Path,
    http_client: httpx.Client | None = None,
) -> FetchResult:
    """Download guideline PDFs to the output directory.

    Skips sources for which the output file already exists (idempotent).

    Args:
        sources: List of guideline sources to fetch.
        output_dir: Directory to write PDF files.
        http_client: Optional HTTP client for testing. Uses httpx.Client if None.

    Returns:
        FetchResult with output_dir, downloaded filenames, and skipped count.

    Raises:
        httpx.HTTPStatusError: When a download returns 4xx/5xx.
        httpx.RequestError: When a network error occurs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] = []
    skipped_files: list[str] = []

    own_client = False
    if http_client is None:
        http_client = httpx.Client(follow_redirects=True, timeout=60.0)
        own_client = True

    try:
        for source in sources:
            out_path = output_dir / source.filename
            if out_path.exists():
                logger.debug("Skipping %s (already exists)", source.filename)
                skipped_files.append(source.filename)
                continue
            logger.info("PDF download start, filename=%s, url=%s", source.filename, source.url)
            t_start = time.perf_counter()
            resp = http_client.get(source.url, follow_redirects=True)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            elapsed_ms = int((time.perf_counter() - t_start) * 1000)
            size_kib = len(resp.content) / 1024
            logger.info(
                "PDF download done, filename=%s, elapsed_ms=%d, size_kib=%.1f",
                source.filename,
                elapsed_ms,
                size_kib,
            )
            downloaded.append(source.filename)
    finally:
        if own_client:
            http_client.close()

    return FetchResult(
        output_dir=output_dir,
        downloaded=tuple(downloaded),
        skipped=len(skipped_files),
        skipped_files=tuple(skipped_files),
    )


def _print_success_report(result: FetchResult, expected_total: int) -> None:
    """Print a success summary: location, counts, and file list.

    Always reports something; highlights when all expected files are present.
    """
    loc = result.output_dir.resolve()
    n_dl = len(result.downloaded)
    n_skip = result.skipped

    def _size_kib(filename: str) -> float:
        p = result.output_dir / filename
        return p.stat().st_size / 1024 if p.exists() else 0.0

    def _file_line(filename: str) -> None:
        print(f"  - {filename} ({_size_kib(filename):.1f} KiB)", flush=True)

    print(f"Location: {loc}", flush=True)
    if n_skip == expected_total and n_dl == 0:
        print(f"All {expected_total} expected files already present.", flush=True)
        if n_skip <= 10:
            for f in result.skipped_files:
                _file_line(f)
        else:
            print(f"  ({n_skip} files - inspect output dir for full list)", flush=True)
    else:
        print(f"Downloaded: {n_dl} file(s)", flush=True)
        if n_skip:
            print(f"Skipped: {n_skip} (already present)", flush=True)
        if n_dl <= 10 and n_dl:
            for f in result.downloaded:
                _file_line(f)
        elif n_dl:
            print("  (10+ files - inspect output dir for full list)", flush=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch clinical guideline PDFs for RAG ingestion",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for PDFs",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    args = parse_args(argv)
    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    args.output.mkdir(parents=True, exist_ok=True)
    try:
        result = fetch_healthcare_guidelines(
            sources=DEFAULT_NHG_SOURCES,
            output_dir=args.output,
        )
        if not args.quiet:
            _print_success_report(result, expected_total=len(DEFAULT_NHG_SOURCES))
        return 0
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.error("Fetch failed: %s", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
