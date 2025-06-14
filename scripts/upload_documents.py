#!/usr/bin/env python3
"""Batch document upload utility.

This script uploads one or more documents to the `/api/documents/upload`
endpoint of the FastAPI application. It supports directory traversal,
custom filename metadata, and basic filtering. The implementation
aligns with STORY-002 and TASK-023, allowing quick ingestion of local
files for chunking and embedding. See docs/technical/CHUNKING.md for
background on the processing pipeline.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterable
from pathlib import Path

import httpx

DEFAULT_API_URL = "http://localhost:8000/api/documents/upload"
DEFAULT_PARAM_SET = "fast"

logger = logging.getLogger(__name__)


class UploadError(Exception):
    """Raised when an upload fails."""


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload documents for RAG processing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("paths", nargs="+", help="Files or directories to upload")

    recurse_group = parser.add_mutually_exclusive_group()
    recurse_group.add_argument("--recurse", action="store_true", help="Recurse into directories")
    recurse_group.add_argument("--norecurse", action="store_true", help="Do not recurse into directories")

    name_group = parser.add_mutually_exclusive_group()
    name_group.add_argument("--fullpath", action="store_true", help="Store absolute path in metadata")
    name_group.add_argument("--relativepath", action="store_true", help="Store path relative to current directory")
    name_group.add_argument("--filenameonly", action="store_true", help="Store only the filename")

    parser.add_argument(
        "--filter",
        nargs="*",
        default=None,
        help="File extensions to upload, e.g. --filter pdf txt",
    )
    parser.add_argument(
        "--parameterset",
        default=DEFAULT_PARAM_SET,
        help="Parameter set for chunking/embedding",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Upload API endpoint")
    parser.add_argument("--haltonerror", action="store_true", help="Stop processing on first error")
    parser.add_argument("--quiet", action="store_true", help="Suppress informational output")

    return parser.parse_args(argv)


def iter_files(paths: Iterable[str], recurse: bool, filters: set[str] | None) -> Iterable[Path]:
    """Yield files from provided paths respecting recursion and filters."""
    visited_dirs: set[Path] = set()

    def handle_dir(dir_path: Path) -> Iterable[Path]:
        real = dir_path.resolve()
        if real in visited_dirs:
            logger.warning("Skipping already visited directory %s", dir_path)
            return []
        visited_dirs.add(real)

        for entry in dir_path.iterdir():
            if entry.is_dir() and recurse:
                if entry.is_symlink():
                    logger.warning("Skipping symlinked directory %s", entry)
                    continue
                yield from handle_dir(entry)
            elif entry.is_file():
                if not filters or entry.suffix.lower().lstrip(".") in filters:
                    yield entry

    for p in paths:
        path = Path(p)
        if path.is_dir():
            yield from handle_dir(path)
        elif path.is_file():
            if not filters or path.suffix.lower().lstrip(".") in filters:
                yield path
        else:
            logger.warning("Path not found: %s", path)


def build_upload_name(path: Path, mode: str, base: Path) -> str:
    """Return the filename to send to the server based on the mode."""
    if mode == "fullpath":
        return str(path.resolve())
    if mode == "filenameonly":
        return path.name
    # relativepath
    try:
        return str(path.resolve().relative_to(base))
    except ValueError:
        return path.name


def upload_file(path: Path, upload_name: str, api_url: str, params_name: str) -> None:
    """Upload a single file to the API."""
    with open(path, "rb") as f:
        files = {"file": (upload_name, f)}
        data = {"params_name": params_name}
        resp = httpx.post(api_url, files=files, data=data, timeout=60)
        if resp.status_code != 200:
            raise UploadError(f"{path}: {resp.status_code} {resp.text}")


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)

    if args.fullpath:
        mode = "fullpath"
    elif args.filenameonly:
        mode = "filenameonly"
    else:
        mode = "relativepath"

    filters = {ext.lower().lstrip(".") for ext in args.filter} if args.filter else None
    base_dir = Path.cwd()

    files = list(iter_files(args.paths, recurse=args.recurse, filters=filters))
    if not files and not args.quiet:
        print("No files found to upload")
        return 1

    for file_path in files:
        upload_name = build_upload_name(file_path, mode, base_dir)
        if not args.quiet:
            print(f"Uploading {file_path} as {upload_name}...")
        try:
            upload_file(file_path, upload_name, args.api_url, args.parameterset)
        except Exception as exc:  # pragma: no cover - runtime errors
            if args.haltonerror:
                raise
            logger.error("Failed to upload %s: %s", file_path, exc)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
