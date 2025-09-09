"""Embedding caching system for the RAG pipeline.

This module provides caching functionality for embeddings to improve performance
and reduce computational costs for repeated text processing.

Features:
- Content-based caching using SHA-256 hashes
- Configurable cache policies (LRU, TTL, size-based)
- Persistent cache storage
- Cache statistics and monitoring
- Thread-safe operations
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import sqlite3
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class CachePolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"  # Least Recently Used
    TTL = "ttl"  # Time To Live
    SIZE = "size"  # Size-based eviction


@dataclass
class CacheEntry:
    """A single cache entry."""

    content_hash: str
    embedding: list[float]
    model_name: str
    created_at: float
    last_accessed: float
    access_count: int
    content_length: int


@dataclass
class CacheStats:
    """Cache statistics."""

    total_entries: int
    total_hits: int
    total_misses: int
    hit_rate: float
    total_size_bytes: int
    oldest_entry: Optional[float]
    newest_entry: Optional[float]


class EmbeddingCache:
    """Thread-safe embedding cache with configurable policies."""

    def __init__(
        self,
        cache_dir: str | Path,
        max_size: int = 10000,
        max_size_bytes: int = 1024 * 1024 * 1024,  # 1GB
        ttl_seconds: int = 7 * 24 * 3600,  # 7 days
        policy: CachePolicy = CachePolicy.LRU,
    ):
        """Initialize the embedding cache.

        Args:
            cache_dir: Directory to store cache files
            max_size: Maximum number of entries
            max_size_bytes: Maximum cache size in bytes
            ttl_seconds: Time-to-live for entries in seconds
            policy: Cache eviction policy
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.max_size = max_size
        self.max_size_bytes = max_size_bytes
        self.ttl_seconds = ttl_seconds
        self.policy = policy

        # Thread safety
        self._lock = threading.RLock()

        # In-memory cache (OrderedDict for LRU)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

        # Database for persistent storage
        self._db_path = self.cache_dir / "embedding_cache.db"
        self._init_database()

        # Load existing cache
        self._load_cache()

        logger.info(
            "Embedding cache initialized",
            cache_dir=str(self.cache_dir),
            max_size=max_size,
            max_size_bytes=max_size_bytes,
            policy=policy.value,
        )

    def _init_database(self) -> None:
        """Initialize the SQLite database for persistent storage."""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    content_hash TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    model_name TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER NOT NULL,
                    content_length INTEGER NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
            """)

    def _load_cache(self) -> None:
        """Load cache entries from database."""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    cursor = conn.execute("""
                        SELECT content_hash, embedding, model_name, created_at,
                               last_accessed, access_count, content_length
                        FROM cache_entries
                        ORDER BY last_accessed DESC
                    """)

                    for row in cursor.fetchall():
                        content_hash, embedding_blob, model_name, created_at, last_accessed, access_count, content_length = row

                        # Deserialize embedding
                        embedding = pickle.loads(embedding_blob)

                        entry = CacheEntry(
                            content_hash=content_hash,
                            embedding=embedding,
                            model_name=model_name,
                            created_at=created_at,
                            last_accessed=last_accessed,
                            access_count=access_count,
                            content_length=content_length,
                        )

                        self._cache[content_hash] = entry

                logger.debug(f"Loaded {len(self._cache)} entries from cache database")

            except Exception as e:
                logger.error(f"Failed to load cache from database: {e}")

    def _save_entry_to_db(self, entry: CacheEntry) -> None:
        """Save a cache entry to the database."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries
                    (content_hash, embedding, model_name, created_at, last_accessed, access_count, content_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.content_hash,
                        pickle.dumps(entry.embedding),
                        entry.model_name,
                        entry.created_at,
                        entry.last_accessed,
                        entry.access_count,
                        entry.content_length,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to save cache entry to database: {e}")

    def _remove_entry_from_db(self, content_hash: str) -> None:
        """Remove a cache entry from the database."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM cache_entries WHERE content_hash = ?", (content_hash,))
        except Exception as e:
            logger.error(f"Failed to remove cache entry from database: {e}")

    def _compute_content_hash(self, text: str, model_name: str) -> str:
        """Compute hash for text content and model combination."""
        content = f"{text}:{model_name}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _should_evict(self) -> bool:
        """Check if cache should evict entries."""
        if len(self._cache) >= self.max_size:
            return True

        if self.policy == CachePolicy.SIZE:
            total_size = sum(entry.content_length for entry in self._cache.values())
            if total_size >= self.max_size_bytes:
                return True

        return False

    def _evict_entries(self) -> None:
        """Evict entries based on the cache policy."""
        if not self._should_evict():
            return

        current_time = time.time()
        entries_to_remove = []

        if self.policy == CachePolicy.LRU:
            # Remove least recently used entries
            while self._should_evict() and self._cache:
                content_hash, entry = self._cache.popitem(last=False)
                entries_to_remove.append(content_hash)

        elif self.policy == CachePolicy.TTL:
            # Remove expired entries
            for content_hash, entry in list(self._cache.items()):
                if current_time - entry.created_at > self.ttl_seconds:
                    del self._cache[content_hash]
                    entries_to_remove.append(content_hash)
                    if not self._should_evict():
                        break

        elif self.policy == CachePolicy.SIZE:
            # Remove largest entries first
            sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].content_length, reverse=True)

            while self._should_evict() and sorted_entries:
                content_hash, entry = sorted_entries.pop(0)
                if content_hash in self._cache:
                    del self._cache[content_hash]
                    entries_to_remove.append(content_hash)

        # Remove from database
        for content_hash in entries_to_remove:
            self._remove_entry_from_db(content_hash)

        self._stats["evictions"] += len(entries_to_remove)

        if entries_to_remove:
            logger.debug(f"Evicted {len(entries_to_remove)} cache entries")

    def get(self, text: str, model_name: str) -> Optional[list[float]]:
        """Get embedding from cache.

        Args:
            text: Text content
            model_name: Name of the embedding model

        Returns:
            Cached embedding if found, None otherwise
        """
        content_hash = self._compute_content_hash(text, model_name)

        with self._lock:
            if content_hash in self._cache:
                entry = self._cache[content_hash]

                # Check TTL
                if self.policy == CachePolicy.TTL:
                    if time.time() - entry.created_at > self.ttl_seconds:
                        del self._cache[content_hash]
                        self._remove_entry_from_db(content_hash)
                        self._stats["misses"] += 1
                        return None

                # Update access information
                entry.last_accessed = time.time()
                entry.access_count += 1

                # Move to end for LRU
                if self.policy == CachePolicy.LRU:
                    self._cache.move_to_end(content_hash)

                # Update database
                self._save_entry_to_db(entry)

                self._stats["hits"] += 1
                logger.debug(f"Cache hit for content hash: {content_hash[:8]}...")
                return entry.embedding

            self._stats["misses"] += 1
            logger.debug(f"Cache miss for content hash: {content_hash[:8]}...")
            return None

    def put(self, text: str, model_name: str, embedding: list[float]) -> None:
        """Store embedding in cache.

        Args:
            text: Text content
            model_name: Name of the embedding model
            embedding: Embedding vector
        """
        content_hash = self._compute_content_hash(text, model_name)
        current_time = time.time()

        entry = CacheEntry(
            content_hash=content_hash,
            embedding=embedding,
            model_name=model_name,
            created_at=current_time,
            last_accessed=current_time,
            access_count=1,
            content_length=len(text),
        )

        with self._lock:
            # Evict if necessary
            self._evict_entries()

            # Store entry
            self._cache[content_hash] = entry
            self._save_entry_to_db(entry)

            logger.debug(f"Cached embedding for content hash: {content_hash[:8]}...")

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

            # Clear database
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
            except Exception as e:
                logger.error(f"Failed to clear cache database: {e}")

            # Reset statistics
            self._stats = {"hits": 0, "misses": 0, "evictions": 0}

            logger.info("Cache cleared")

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

            total_size_bytes = sum(entry.content_length for entry in self._cache.values())

            oldest_entry = min(entry.created_at for entry in self._cache.values()) if self._cache else None
            newest_entry = max(entry.created_at for entry in self._cache.values()) if self._cache else None

            return CacheStats(
                total_entries=len(self._cache),
                total_hits=self._stats["hits"],
                total_misses=self._stats["misses"],
                hit_rate=hit_rate,
                total_size_bytes=total_size_bytes,
                oldest_entry=oldest_entry,
                newest_entry=newest_entry,
            )

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        if self.policy != CachePolicy.TTL:
            return 0

        current_time = time.time()
        expired_hashes = []

        with self._lock:
            for content_hash, entry in list(self._cache.items()):
                if current_time - entry.created_at > self.ttl_seconds:
                    expired_hashes.append(content_hash)

            for content_hash in expired_hashes:
                del self._cache[content_hash]
                self._remove_entry_from_db(content_hash)

        if expired_hashes:
            logger.debug(f"Cleaned up {len(expired_hashes)} expired cache entries")

        return len(expired_hashes)


# Global cache instance
_cache_instance: Optional[EmbeddingCache] = None


def get_embedding_cache() -> EmbeddingCache:
    """Get the global embedding cache instance."""
    global _cache_instance

    if _cache_instance is None:
        cache_dir = Path("cache/embeddings_cache")
        _cache_instance = EmbeddingCache(
            cache_dir=cache_dir,
            max_size=10000,
            max_size_bytes=1024 * 1024 * 1024,  # 1GB
            ttl_seconds=7 * 24 * 3600,  # 7 days
            policy=CachePolicy.LRU,
        )

    return _cache_instance


def clear_embedding_cache() -> None:
    """Clear the global embedding cache."""
    global _cache_instance

    if _cache_instance is not None:
        _cache_instance.clear()


__all__ = [
    "CachePolicy",
    "CacheEntry",
    "CacheStats",
    "EmbeddingCache",
    "get_embedding_cache",
    "clear_embedding_cache",
]
