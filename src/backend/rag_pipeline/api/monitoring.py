"""Monitoring and health check API endpoints for the RAG pipeline.

This module provides endpoints for monitoring system health, performance metrics,
and operational status of the RAG pipeline components.
"""

from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.vector_store import get_vector_store_manager_from_env
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: float
    components: Dict[str, Any]
    overall_health: str


class MetricsResponse(BaseModel):
    """Performance metrics response model."""

    vector_store: Dict[str, Any]
    system: Dict[str, Any]
    timestamp: float


@router.get("/health")
async def health_check() -> HealthResponse:
    """Perform a comprehensive health check of all system components.

    Returns:
        HealthResponse with status of all components
    """
    logger.info("Performing system health check")

    start_time = time.time()
    components = {}
    overall_health = "healthy"

    try:
        # Check vector store health
        vector_store_manager = get_vector_store_manager_from_env()
        vector_store_health = vector_store_manager.health_check()

        components["vector_store"] = {
            "status": vector_store_health.status.value,
            "message": vector_store_health.message,
            "response_time_ms": vector_store_health.response_time_ms,
            "details": vector_store_health.details,
        }

        # Update overall health based on component status
        if vector_store_health.status.value in ["unhealthy", "unknown"]:
            overall_health = "unhealthy"
        elif vector_store_health.status.value == "degraded":
            overall_health = "degraded"

        # Check document storage
        try:
            from ..utils.directory_utils import get_uploaded_files_dir

            upload_dir = get_uploaded_files_dir()
            components["document_storage"] = {
                "status": "healthy" if upload_dir.exists() else "unhealthy",
                "path": str(upload_dir),
                "exists": upload_dir.exists(),
                "writable": upload_dir.is_dir() and upload_dir.stat().st_mode & 0o200,
            }
        except Exception as e:
            components["document_storage"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            overall_health = "unhealthy"

        # Check embedding cache
        try:
            from ..core.embedding_cache import get_embedding_cache

            cache = get_embedding_cache()
            cache_stats = cache.get_stats()

            components["embedding_cache"] = {
                "status": "healthy",
                "total_entries": cache_stats.total_entries,
                "hit_rate": cache_stats.hit_rate,
                "total_size_bytes": cache_stats.total_size_bytes,
            }
        except Exception as e:
            components["embedding_cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            if overall_health == "healthy":
                overall_health = "degraded"

        # Check document obsoletion system
        try:
            from ..core.document_obsoletion import get_obsoletion_manager

            obsoletion_manager = get_obsoletion_manager()
            active_docs = obsoletion_manager.get_active_documents()

            components["document_obsoletion"] = {
                "status": "healthy",
                "active_documents": len(active_docs),
            }
        except Exception as e:
            components["document_obsoletion"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            if overall_health == "healthy":
                overall_health = "degraded"

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        components["system"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        overall_health = "unhealthy"

    response_time = time.time() - start_time

    return HealthResponse(
        status=overall_health,
        timestamp=time.time(),
        components=components,
        overall_health=overall_health,
    )


@router.get("/metrics")
async def get_metrics() -> MetricsResponse:
    """Get performance metrics for system components.

    Returns:
        MetricsResponse with performance data
    """
    logger.info("Retrieving system metrics")

    try:
        # Get vector store metrics
        vector_store_manager = get_vector_store_manager_from_env()
        vector_store_metrics = vector_store_manager.get_metrics()

        vector_store_data = {
            "total_queries": vector_store_metrics.total_queries,
            "total_inserts": vector_store_metrics.total_inserts,
            "total_deletes": vector_store_metrics.total_deletes,
            "avg_query_time_ms": vector_store_metrics.avg_query_time_ms,
            "avg_insert_time_ms": vector_store_metrics.avg_insert_time_ms,
            "avg_delete_time_ms": vector_store_metrics.avg_delete_time_ms,
            "error_count": vector_store_metrics.error_count,
            "last_updated": vector_store_metrics.last_updated,
        }

        # Get system metrics
        import os

        import psutil

        system_data = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "process_memory_mb": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,
        }

        # Get embedding cache metrics
        try:
            from ..core.embedding_cache import get_embedding_cache

            cache = get_embedding_cache()
            cache_stats = cache.get_stats()

            system_data["embedding_cache"] = {
                "total_entries": cache_stats.total_entries,
                "total_hits": cache_stats.total_hits,
                "total_misses": cache_stats.total_misses,
                "hit_rate": cache_stats.hit_rate,
                "total_size_bytes": cache_stats.total_size_bytes,
            }
        except Exception as e:
            system_data["embedding_cache"] = {"error": str(e)}

        return MetricsResponse(
            vector_store=vector_store_data,
            system=system_data,
            timestamp=time.time(),
        )

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.post("/backup")
async def create_backup(backup_path: str = "backups/vector_store_backup") -> Dict[str, Any]:
    """Create a backup of the vector store.

    Args:
        backup_path: Path where to store the backup

    Returns:
        Dict with backup status and information
    """
    logger.info(f"Creating vector store backup: {backup_path}")

    try:
        vector_store_manager = get_vector_store_manager_from_env()
        success = vector_store_manager.backup(backup_path)

        if success:
            return {
                "status": "success",
                "message": f"Backup created successfully at {backup_path}",
                "backup_path": backup_path,
                "timestamp": time.time(),
            }
        else:
            raise HTTPException(status_code=500, detail="Backup creation failed")

    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


@router.post("/restore")
async def restore_backup(backup_path: str) -> Dict[str, Any]:
    """Restore the vector store from a backup.

    Args:
        backup_path: Path to the backup to restore from

    Returns:
        Dict with restore status and information
    """
    logger.info(f"Restoring vector store from backup: {backup_path}")

    try:
        vector_store_manager = get_vector_store_manager_from_env()
        success = vector_store_manager.restore(backup_path)

        if success:
            return {
                "status": "success",
                "message": f"Vector store restored successfully from {backup_path}",
                "backup_path": backup_path,
                "timestamp": time.time(),
            }
        else:
            raise HTTPException(status_code=500, detail="Restore operation failed")

    except Exception as e:
        logger.error(f"Restore operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore operation failed: {str(e)}")


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get a quick status overview of the system.

    Returns:
        Dict with basic system status information
    """
    try:
        # Quick health check
        vector_store_manager = get_vector_store_manager_from_env()
        health = vector_store_manager.health_check()

        return {
            "status": health.status.value,
            "message": health.message,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - time.time(),  # Placeholder - would need startup time tracking
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Status check failed: {str(e)}",
            "timestamp": time.time(),
        }
