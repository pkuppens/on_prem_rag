"""Simple metadata management using SQLite."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, unique=True)
    file_hash: Mapped[str] = mapped_column(String, unique=True)
    pages: Mapped[str] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, default=1)
    obsolete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer)
    model_name: Mapped[str] = mapped_column(String)
    chunk_size: Mapped[int] = mapped_column(Integer)
    chunk_overlap: Mapped[int] = mapped_column(Integer)


@dataclass
class MetadataStore:
    """Manage document and embedding metadata."""

    db_path: str = "data/metadata.db"

    def __post_init__(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_document(self, filename: str, file_hash: str, pages: str, version: int = 1) -> DocumentRecord:
        with self.Session() as session:
            existing = session.query(DocumentRecord).filter_by(file_hash=file_hash).first()
            if existing:
                return existing
            record = DocumentRecord(filename=filename, file_hash=file_hash, pages=pages, version=version)
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def mark_obsolete(self, document_id: int) -> None:
        with self.Session() as session:
            doc = session.get(DocumentRecord, document_id)
            if doc:
                doc.obsolete = True
                session.commit()
