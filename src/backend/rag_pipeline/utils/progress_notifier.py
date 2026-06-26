"""Compatibility layer for progress notification utilities — COMPATIBILITY SHIM.

.. deprecated::
   The canonical implementations now live in ``backend.ingestion.infrastructure.progress``.
   Importing them here keeps older imports working while the codebase migrates.
"""

from backend.rag_pipeline.utils.progress import ProgressEvent, ProgressNotifier, progress_notifier

__all__ = ["ProgressEvent", "ProgressNotifier", "progress_notifier"]
