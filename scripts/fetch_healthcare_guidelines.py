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
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("tmp/healthcare_guidelines")


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
) -> int:
    """Download guideline PDFs to the output directory.

    Skips sources for which the output file already exists (idempotent).

    Args:
        sources: List of guideline sources to fetch.
        output_dir: Directory to write PDF files.
        http_client: Optional HTTP client for testing. Uses httpx.Client if None.

    Returns:
        Number of files downloaded (excluding skipped).

    Raises:
        httpx.HTTPStatusError: When a download returns 4xx/5xx.
        httpx.RequestError: When a network error occurs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    own_client = False
    if http_client is None:
        http_client = httpx.Client(follow_redirects=True, timeout=60.0)
        own_client = True

    try:
        for source in sources:
            out_path = output_dir / source.filename
            if out_path.exists():
                logger.debug("Skipping %s (already exists)", source.filename)
                continue
            logger.info("Downloading %s", source.title)
            resp = http_client.get(source.url, follow_redirects=True)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)
            downloaded += 1
    finally:
        if own_client:
            http_client.close()

    return downloaded


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
        count = fetch_healthcare_guidelines(
            sources=DEFAULT_NHG_SOURCES,
            output_dir=args.output,
        )
        if not args.quiet:
            logger.info("Downloaded %d file(s) to %s", count, args.output)
        return 0
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.error("Fetch failed: %s", e)
        return 1
