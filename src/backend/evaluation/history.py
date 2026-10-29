"""Persisted history of evaluation runs.

Each run of the evaluation CLI appends one JSON line per retrieval config to a JSONL file, tagged with a
shared run_id and UTC timestamp. Runs can then be compared over time (e.g. across embedding models);
the file is the input for the eval-comparison dbt mart (#188).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_HISTORY_PATH = Path("tmp/eval-runs/history.jsonl")


def build_history_rows(
    report: dict[str, dict[str, Any]],
    *,
    dataset: str,
    embedding_model: str,
    top_k: int,
    run_id: str | None = None,
    run_timestamp: datetime | None = None,
) -> list[dict[str, Any]]:
    """Flatten a run_evaluation report into one history row per retrieval config.

    Args:
        report: Output of run_evaluation: config_name -> {'results': [...], 'aggregates': {...}}.
        dataset: Name of the benchmark dataset (typically its file name).
        embedding_model: Embedding model the vector store was built with.
        top_k: Retrieval top-k used for the run.
        run_id: Identifier shared by all rows of this run. Default: a new uuid4.
        run_timestamp: When the run happened. Default: now (UTC).

    Returns:
        List of flat dicts with run metadata and the config's aggregate metrics.
    """
    run_id = run_id or str(uuid.uuid4())
    timestamp = (run_timestamp or datetime.now(UTC)).isoformat()
    return [
        {
            "run_id": run_id,
            "run_timestamp": timestamp,
            "dataset": dataset,
            "embedding_model": embedding_model,
            "retrieval_config": config_name,
            "top_k": top_k,
            **data.get("aggregates", {}),
        }
        for config_name, data in report.items()
    ]


def append_history(rows: list[dict[str, Any]], history_path: str | Path = DEFAULT_HISTORY_PATH) -> Path:
    """Append rows as JSON lines to the history file, creating it and its directory if needed.

    Returns:
        Path of the history file.
    """
    path = Path(history_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return path


def read_history(history_path: str | Path = DEFAULT_HISTORY_PATH) -> list[dict[str, Any]]:
    """Read all rows from the history file; empty list if it does not exist yet."""
    path = Path(history_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
