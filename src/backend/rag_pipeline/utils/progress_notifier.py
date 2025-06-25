"""Compatibility layer for progress notification utilities."""

# This module previously contained the implementation of ``ProgressEvent`` and
# ``ProgressNotifier``.  They now live in :mod:`backend.rag_pipeline.utils.progress`.
# Importing them here keeps older imports working while the codebase migrates.

from .progress import ProgressEvent, ProgressNotifier, progress_notifier

__all__ = ["ProgressEvent", "ProgressNotifier", "progress_notifier"]
