"""Utilities to inspect ChromaDB schema.

See docs/technical/CHROMADB_SCHEMA.md for details.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def is_fts5_available() -> bool:
    """Check if SQLite FTS5 extension is available.

    Returns:
        bool: True if FTS5 is available, False otherwise.
    """
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE test_fts USING fts5(content)")
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False


def inspect_chroma_schema(persist_dir: str | Path) -> dict[str, list[tuple[str, str]]]:
    """Return ChromaDB table structure as {table: [(col, type), ...]}"""
    persist_dir = Path(persist_dir)
    db_path = persist_dir / "chroma.sqlite3"
    if not db_path.exists():
        raise FileNotFoundError(f"Chroma database not found at {db_path}")

    # Check if FTS5 is available before attempting to connect
    if not is_fts5_available():
        raise RuntimeError(
            "SQLite FTS5 extension not available. This is required for ChromaDB. "
            "In CI environments, consider using a different SQLite build or skipping this test."
        )

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables: dict[str, list[tuple[str, str]]] = {}
    for (name,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        cols = [(row[1], row[2]) for row in conn.execute(f"PRAGMA table_info('{name}')")]
        tables[name] = cols
    conn.close()
    return tables


__all__ = ["inspect_chroma_schema", "is_fts5_available"]
