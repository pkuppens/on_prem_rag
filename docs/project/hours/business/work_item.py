"""
Work Item Business Model

This module defines the WorkItem business entity for representing
individual work items such as Git commits, document edits, code reviews, etc.

Business Domain: Work Session Management
Entity: WorkItem
Purpose: Represent individual work items that occur during work sessions
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class WorkItem:
    """Represents an individual work item that occurred during a work session.

    This business entity models individual work items such as Git commits,
    document edits, code reviews, and other work activities that can be
    associated with work sessions for comprehensive work tracking.

    Business Rules:
    - Work items must have valid timestamps
    - Work items must be associated with a work session
    - Work item types must be recognized and categorized

    Attributes:
        work_item_id: Unique identifier for the work item
        work_item_type: Type of work item (e.g., "commit", "review", "document")
        timestamp: When the work item occurred
        session_id: ID of the work session this item belongs to
        title: Title or summary of the work item
        description: Detailed description of the work item
        repository: Repository or project where work occurred (optional)
        branch: Git branch where work occurred (optional)
        commit_hash: Git commit hash (for commits)
        files_changed: List of files changed (optional)
        lines_added: Number of lines added (optional)
        lines_deleted: Number of lines deleted (optional)
        author: Author of the work item
        confidence_score: Confidence in work item detection (0.0-1.0)
        metadata: Additional metadata as key-value pairs
    """

    # Core identification
    work_item_id: str
    work_item_type: str
    timestamp: str  # Flexible string format for timestamp
    session_id: str  # Associated work session ID

    # Work item content
    title: str
    description: Optional[str] = None

    # Git-specific attributes (for commits)
    repository: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    files_changed: Optional[list] = None
    lines_added: Optional[int] = None
    lines_deleted: Optional[int] = None

    # Author and confidence
    author: Optional[str] = None
    confidence_score: Optional[float] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Set default confidence score if not provided
        if self.confidence_score is None:
            self.confidence_score = 1.0

        # Initialize metadata if not provided
        if self.metadata is None:
            self.metadata = {}

        # Initialize files_changed if not provided
        if self.files_changed is None:
            self.files_changed = []

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the work item.

        Args:
            key: Metadata key
            value: Metadata value
        """
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def get_impact_score(self) -> float:
        """Calculate impact score based on lines changed and files modified.

        Returns:
            Impact score (0.0-1.0) based on work item size
        """
        if self.lines_added is None and self.lines_deleted is None:
            return 0.0

        total_lines = (self.lines_added or 0) + (self.lines_deleted or 0)
        file_count = len(self.files_changed) if self.files_changed else 0

        # Simple impact calculation: normalize by typical commit size
        # This can be refined based on project-specific metrics
        impact = min(1.0, (total_lines / 100.0) + (file_count / 10.0))
        return impact

    def to_dict(self) -> Dict[str, Any]:
        """Convert WorkItem to dictionary representation.

        Returns:
            Dictionary representation of the WorkItem
        """
        return {
            "work_item_id": self.work_item_id,
            "work_item_type": self.work_item_type,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "repository": self.repository,
            "branch": self.branch,
            "commit_hash": self.commit_hash,
            "files_changed": self.files_changed,
            "lines_added": self.lines_added,
            "lines_deleted": self.lines_deleted,
            "author": self.author,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
            "impact_score": self.get_impact_score(),
        }
