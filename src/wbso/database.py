"""WBSO database models and connection management.

This module provides SQLAlchemy models for normalized WBSO data storage
and database connection management following the project's SQLite + SQLAlchemy architecture.

See docs/technical/WBSO_DATABASE_SCHEMA.md for detailed schema design and relationships.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, sessionmaker

from backend.rag_pipeline.utils.directory_utils import ensure_directory_exists, get_database_dir

# Ensure database directory exists
database_dir = get_database_dir()
ensure_directory_exists(database_dir)

# Database configuration
DATABASE_URL = f"sqlite:///{database_dir / 'wbso.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class Repository(Base):
    """Repository information for WBSO sessions."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    work_sessions: Mapped[List["WorkSession"]] = relationship("WorkSession", back_populates="repository")
    commits: Mapped[List["Commit"]] = relationship("Commit", back_populates="repository")


class WBSOCategory(Base):
    """WBSO categories with descriptions and justifications."""

    __tablename__ = "wbso_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    justification_template: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    work_sessions: Mapped[List["WorkSession"]] = relationship("WorkSession", back_populates="wbso_category")


class WorkSession(Base):
    """Work session with WBSO classification and validation."""

    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    work_hours: Mapped[float] = mapped_column(String(10), nullable=False)  # Using String for DECIMAL precision
    duration_hours: Mapped[float] = mapped_column(String(10), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD format
    session_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_wbso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wbso_category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wbso_categories.id"))
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    repository_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("repositories.id"))
    wbso_justification: Mapped[Optional[str]] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(String(5), default="1.0")
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    repository: Mapped[Optional["Repository"]] = relationship("Repository", back_populates="work_sessions")
    wbso_category: Mapped[Optional["WBSOCategory"]] = relationship("WBSOCategory", back_populates="work_sessions")
    commits: Mapped[List["Commit"]] = relationship("Commit", back_populates="session")
    calendar_events: Mapped[List["CalendarEvent"]] = relationship("CalendarEvent", back_populates="session")
    validation_results: Mapped[List["ValidationResult"]] = relationship("ValidationResult", back_populates="session")


class Commit(Base):
    """Git commits associated with work sessions."""

    __tablename__ = "commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repository_id: Mapped[int] = mapped_column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("work_sessions.session_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="commits")
    session: Mapped[Optional["WorkSession"]] = relationship("WorkSession", back_populates="commits")


class CalendarEvent(Base):
    """Google Calendar events for WBSO sessions."""

    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("work_sessions.session_id"), nullable=False)
    google_event_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    color_id: Mapped[str] = mapped_column(String(10), default="1")
    location: Mapped[str] = mapped_column(String(255), default="Home Office")
    transparency: Mapped[str] = mapped_column(String(20), default="opaque")
    uploaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    session: Mapped["WorkSession"] = relationship("WorkSession", back_populates="calendar_events")


class ValidationResult(Base):
    """Validation results for work sessions."""

    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255), ForeignKey("work_sessions.session_id"), nullable=False)
    validation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    warning_message: Mapped[Optional[str]] = mapped_column(Text)
    validated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["WorkSession"] = relationship("WorkSession", back_populates="validation_results")


def init_wbso_database() -> None:
    """Initialize the WBSO database with all tables."""
    Base.metadata.create_all(bind=engine)


def get_wbso_session() -> Session:
    """Get a database session for WBSO operations."""
    return SessionLocal()


def close_wbso_session(session: Session) -> None:
    """Close a database session."""
    session.close()


# Initialize database on module import
init_wbso_database()
