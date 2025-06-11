"""Utilities to inspect ChromaDB schema.

See docs/technical/CHROMADB_SCHEMA.md for details.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def inspect_chroma_schema(persist_dir: str | Path) -> dict[str, list[tuple[str, str]]]:
    """Return ChromaDB table structure as {table: [(col, type), ...]}"""
    persist_dir = Path(persist_dir)
    db_path = persist_dir / "chroma.sqlite3"
    if not db_path.exists():
        raise FileNotFoundError(f"Chroma database not found at {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables: dict[str, list[tuple[str, str]]] = {}
    for (name,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        cols = [(row[1], row[2]) for row in conn.execute(f"PRAGMA table_info('{name}')")]
        tables[name] = cols
    conn.close()
    return tables

__all__ = ["inspect_chroma_schema"]
