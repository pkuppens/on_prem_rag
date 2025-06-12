"""Natural language to SQL conversion pipeline.

Part of [FEAT-004](../../../project/program/features/FEAT-004.md).
"""

from __future__ import annotations

from typing import Any


def nl_to_sql_pipeline(question: str, schema: str, user_roles: list[str]) -> dict[str, Any]:
    """Convert natural language question to SQL.

    This is a simplified placeholder implementation.
    TODO: integrate with LLM provider for full NL2SQL support.
    """
    sql = f"SELECT * FROM table WHERE question = '{question}'"
    return {"sql": sql, "results": [], "explanation": "TODO"}
