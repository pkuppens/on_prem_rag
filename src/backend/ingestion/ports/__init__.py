"""Ports (interfaces) for the Ingestion Bounded Context.

These define the contracts that the Ingestion BC depends on
from other bounded contexts or external systems.
"""

from backend.retrieval.domain.interfaces import IVectorStoreWrite

__all__ = ["IVectorStoreWrite"]
