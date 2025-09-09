"""Document obsoletion and invalidation system for the RAG pipeline.

This module provides functionality for managing document lifecycle, including
obsoletion, invalidation, and versioning of documents in the vector store.

Features:
- Document versioning and history tracking
- Obsoletion with validity periods
- Batch invalidation operations
- Soft and hard deletion support
- Audit trail for document changes
"""

from __future__ import annotations

import logging
import sqlite3
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class DocumentStatus(Enum):
    """Document status enumeration."""

    ACTIVE = "active"
    OBSOLETE = "obsolete"
    INVALID = "invalid"
    DELETED = "deleted"


@dataclass
class DocumentVersion:
    """Document version information."""

    document_id: str
    version: int
    file_path: str
    file_hash: str
    created_at: float
    valid_from: float
    valid_until: Optional[float]
    status: DocumentStatus
    metadata: dict[str, Any]


@dataclass
class ObsoletionEvent:
    """Document obsoletion event."""

    document_id: str
    version: int
    obsoleted_at: float
    reason: str
    obsoleted_by: str
    metadata: dict[str, Any]


class DocumentObsoletionManager:
    """Manages document obsoletion and versioning."""

    def __init__(self, db_path: str | Path):
        """Initialize the document obsoletion manager.

        Args:
            db_path: Path to the SQLite database for tracking
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()

        logger.info(f"Document obsoletion manager initialized: {self.db_path}")

    def _init_database(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            # Document versions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_versions (
                    document_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    valid_from REAL NOT NULL,
                    valid_until REAL,
                    status TEXT NOT NULL,
                    metadata TEXT,
                    PRIMARY KEY (document_id, version)
                )
            """)

            # Obsoletion events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS obsoletion_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    obsoleted_at REAL NOT NULL,
                    reason TEXT NOT NULL,
                    obsoleted_by TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Indexes for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_status
                ON document_versions(document_id, status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_valid_period
                ON document_versions(valid_from, valid_until)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_obsoletion_document
                ON obsoletion_events(document_id, version)
            """)

    def register_document(
        self,
        document_id: str,
        file_path: str,
        file_hash: str,
        valid_from: Optional[float] = None,
        valid_until: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> int:
        """Register a new document version.

        Args:
            document_id: Unique document identifier
            file_path: Path to the document file
            file_hash: SHA-256 hash of the document
            valid_from: When the document becomes valid (default: now)
            valid_until: When the document becomes invalid (default: never)
            metadata: Additional metadata

        Returns:
            Version number of the registered document
        """
        current_time = time.time()
        valid_from = valid_from or current_time

        # Get next version number
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT MAX(version) FROM document_versions
                WHERE document_id = ?
            """,
                (document_id,),
            )

            max_version = cursor.fetchone()[0]
            next_version = (max_version or 0) + 1

            # Insert new version
            conn.execute(
                """
                INSERT INTO document_versions
                (document_id, version, file_path, file_hash, created_at,
                 valid_from, valid_until, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    document_id,
                    next_version,
                    file_path,
                    file_hash,
                    current_time,
                    valid_from,
                    valid_until,
                    DocumentStatus.ACTIVE.value,
                    str(metadata) if metadata else None,
                ),
            )

        logger.info(
            f"Registered document version",
            document_id=document_id,
            version=next_version,
            file_path=file_path,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        return next_version

    def obsolete_document(
        self,
        document_id: str,
        version: Optional[int] = None,
        reason: str = "Manual obsoletion",
        obsoleted_by: str = "system",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Mark a document version as obsolete.

        Args:
            document_id: Document identifier
            version: Version to obsolete (default: latest)
            reason: Reason for obsoletion
            obsoleted_by: Who/what obsoleted the document
            metadata: Additional metadata
        """
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            # Get version to obsolete
            if version is None:
                cursor = conn.execute(
                    """
                    SELECT version FROM document_versions
                    WHERE document_id = ? AND status = ?
                    ORDER BY version DESC LIMIT 1
                """,
                    (document_id, DocumentStatus.ACTIVE.value),
                )

                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"No active version found for document: {document_id}")
                version = result[0]

            # Update document status
            conn.execute(
                """
                UPDATE document_versions
                SET status = ?, valid_until = ?
                WHERE document_id = ? AND version = ?
            """,
                (DocumentStatus.OBSOLETE.value, current_time, document_id, version),
            )

            # Record obsoletion event
            conn.execute(
                """
                INSERT INTO obsoletion_events
                (document_id, version, obsoleted_at, reason, obsoleted_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    document_id,
                    version,
                    current_time,
                    reason,
                    obsoleted_by,
                    str(metadata) if metadata else None,
                ),
            )

        logger.info(
            f"Obsoleted document version", document_id=document_id, version=version, reason=reason, obsoleted_by=obsoleted_by
        )

    def invalidate_document(
        self,
        document_id: str,
        version: Optional[int] = None,
        reason: str = "Manual invalidation",
        invalidated_by: str = "system",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Mark a document version as invalid.

        Args:
            document_id: Document identifier
            version: Version to invalidate (default: latest)
            reason: Reason for invalidation
            invalidated_by: Who/what invalidated the document
            metadata: Additional metadata
        """
        current_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            # Get version to invalidate
            if version is None:
                cursor = conn.execute(
                    """
                    SELECT version FROM document_versions
                    WHERE document_id = ? AND status = ?
                    ORDER BY version DESC LIMIT 1
                """,
                    (document_id, DocumentStatus.ACTIVE.value),
                )

                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"No active version found for document: {document_id}")
                version = result[0]

            # Update document status
            conn.execute(
                """
                UPDATE document_versions
                SET status = ?, valid_until = ?
                WHERE document_id = ? AND version = ?
            """,
                (DocumentStatus.INVALID.value, current_time, document_id, version),
            )

            # Record obsoletion event
            conn.execute(
                """
                INSERT INTO obsoletion_events
                (document_id, version, obsoleted_at, reason, obsoleted_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    document_id,
                    version,
                    current_time,
                    reason,
                    invalidated_by,
                    str(metadata) if metadata else None,
                ),
            )

        logger.info(
            f"Invalidated document version", document_id=document_id, version=version, reason=reason, invalidated_by=invalidated_by
        )

    def get_active_documents(self, current_time: Optional[float] = None) -> list[DocumentVersion]:
        """Get all currently active documents.

        Args:
            current_time: Time to check validity (default: now)

        Returns:
            List of active document versions
        """
        current_time = current_time or time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT document_id, version, file_path, file_hash, created_at,
                       valid_from, valid_until, status, metadata
                FROM document_versions
                WHERE status = ?
                AND valid_from <= ?
                AND (valid_until IS NULL OR valid_until > ?)
                ORDER BY document_id, version DESC
            """,
                (DocumentStatus.ACTIVE.value, current_time, current_time),
            )

            documents = []
            for row in cursor.fetchall():
                document_id, version, file_path, file_hash, created_at, valid_from, valid_until, status, metadata_str = row

                metadata = eval(metadata_str) if metadata_str else {}

                documents.append(
                    DocumentVersion(
                        document_id=document_id,
                        version=version,
                        file_path=file_path,
                        file_hash=file_hash,
                        created_at=created_at,
                        valid_from=valid_from,
                        valid_until=valid_until,
                        status=DocumentStatus(status),
                        metadata=metadata,
                    )
                )

        return documents

    def get_document_history(self, document_id: str) -> list[DocumentVersion]:
        """Get version history for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of document versions in chronological order
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT document_id, version, file_path, file_hash, created_at,
                       valid_from, valid_until, status, metadata
                FROM document_versions
                WHERE document_id = ?
                ORDER BY version ASC
            """,
                (document_id,),
            )

            documents = []
            for row in cursor.fetchall():
                document_id, version, file_path, file_hash, created_at, valid_from, valid_until, status, metadata_str = row

                metadata = eval(metadata_str) if metadata_str else {}

                documents.append(
                    DocumentVersion(
                        document_id=document_id,
                        version=version,
                        file_path=file_path,
                        file_hash=file_hash,
                        created_at=created_at,
                        valid_from=valid_from,
                        valid_until=valid_until,
                        status=DocumentStatus(status),
                        metadata=metadata,
                    )
                )

        return documents

    def get_obsoletion_events(
        self,
        document_id: Optional[str] = None,
        since: Optional[float] = None,
    ) -> list[ObsoletionEvent]:
        """Get obsoletion events.

        Args:
            document_id: Filter by document ID (optional)
            since: Filter events since this timestamp (optional)

        Returns:
            List of obsoletion events
        """
        query = """
            SELECT document_id, version, obsoleted_at, reason, obsoleted_by, metadata
            FROM obsoletion_events
            WHERE 1=1
        """
        params = []

        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)

        if since:
            query += " AND obsoleted_at >= ?"
            params.append(since)

        query += " ORDER BY obsoleted_at DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)

            events = []
            for row in cursor.fetchall():
                document_id, version, obsoleted_at, reason, obsoleted_by, metadata_str = row

                metadata = eval(metadata_str) if metadata_str else {}

                events.append(
                    ObsoletionEvent(
                        document_id=document_id,
                        version=version,
                        obsoleted_at=obsoleted_at,
                        reason=reason,
                        obsoleted_by=obsoleted_by,
                        metadata=metadata,
                    )
                )

        return events

    def cleanup_expired_documents(self, current_time: Optional[float] = None) -> int:
        """Mark expired documents as obsolete.

        Args:
            current_time: Time to check expiration (default: now)

        Returns:
            Number of documents marked as obsolete
        """
        current_time = current_time or time.time()

        with sqlite3.connect(self.db_path) as conn:
            # Find expired active documents
            cursor = conn.execute(
                """
                SELECT document_id, version FROM document_versions
                WHERE status = ?
                AND valid_until IS NOT NULL
                AND valid_until <= ?
            """,
                (DocumentStatus.ACTIVE.value, current_time),
            )

            expired_docs = cursor.fetchall()

            # Mark as obsolete
            for document_id, version in expired_docs:
                conn.execute(
                    """
                    UPDATE document_versions
                    SET status = ?
                    WHERE document_id = ? AND version = ?
                """,
                    (DocumentStatus.OBSOLETE.value, document_id, version),
                )

                # Record obsoletion event
                conn.execute(
                    """
                    INSERT INTO obsoletion_events
                    (document_id, version, obsoleted_at, reason, obsoleted_by, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        document_id,
                        version,
                        current_time,
                        "Expired automatically",
                        "system",
                        None,
                    ),
                )

        if expired_docs:
            logger.info(f"Marked {len(expired_docs)} expired documents as obsolete")

        return len(expired_docs)


# Global obsoletion manager instance
_obsoletion_manager: Optional[DocumentObsoletionManager] = None


def get_obsoletion_manager() -> DocumentObsoletionManager:
    """Get the global document obsoletion manager."""
    global _obsoletion_manager

    if _obsoletion_manager is None:
        db_path = Path("data/database/document_obsoletion.db")
        _obsoletion_manager = DocumentObsoletionManager(db_path)

    return _obsoletion_manager


__all__ = [
    "DocumentStatus",
    "DocumentVersion",
    "ObsoletionEvent",
    "DocumentObsoletionManager",
    "get_obsoletion_manager",
]
