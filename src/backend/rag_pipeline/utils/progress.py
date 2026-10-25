"""Progress notification utilities — COMPATIBILITY SHIM.

.. deprecated::
   The canonical implementation lives in ``backend.ingestion.infrastructure.progress``.
   This module re-exports it so that the upload endpoints, the WebSocket endpoint and the
   ingestion service all share one ``progress_notifier`` instance. Two separate instances
   meant WebSocket subscribers never saw processing or completion events (#217).
"""

from backend.ingestion.infrastructure.progress import ProgressEvent, ProgressNotifier, progress_notifier

__all__ = ["ProgressEvent", "ProgressNotifier", "progress_notifier"]
