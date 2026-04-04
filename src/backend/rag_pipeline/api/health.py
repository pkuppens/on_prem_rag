# src/backend/rag_pipeline/api/health.py
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from ..config.llm_config import get_llm_config
from ..core.llm_providers import get_llm_provider_from_env
from ..core.vector_store import get_vector_store_manager

router = APIRouter()


@router.get("/health")
async def health():
    """General health check endpoint for backward compatibility."""
    return JSONResponse(content={"status": "ok"})


@router.get("/api/v1/health")
async def health_v1_api(deep: bool = False):
    """Versioned API health: shallow status or optional deep component rollup."""

    if not deep:
        return JSONResponse(content={"status": "ok"})

    components: dict = {}
    try:
        get_vector_store_manager()
        components["database"] = {"status": "ok"}
    except Exception as e:
        components["database"] = {"status": "error", "detail": str(e)}

    try:
        llm_config = get_llm_config()
        llm_provider = get_llm_provider_from_env()
        is_healthy = await llm_provider.health_check()
        components["llm"] = {"status": "ok" if is_healthy else "error", "backend": llm_config.backend_model_pair}
    except Exception as e:
        components["llm"] = {"status": "error", "detail": str(e)}

    try:
        get_vector_store_manager()
        components["vector"] = {"status": "ok"}
    except Exception as e:
        components["vector"] = {"status": "error", "detail": str(e)}

    components["auth"] = {"status": "ok"}
    components["websocket"] = {"status": "ok"}

    any_err = any(c.get("status") == "error" for c in components.values())
    return JSONResponse(content={"status": "degraded" if any_err else "ok", "components": components})


@router.get("/api/v1/health/database")
async def health_database():
    """Check the health of the database connection."""
    # For now, we'll assume the database is healthy since we're using ChromaDB
    # which doesn't require a separate database connection
    try:
        # Try to access the vector store to verify it's working
        get_vector_store_manager()
        # If we can create the vector store manager, the database is healthy
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")


@router.get("/api/v1/health/llm")
async def health_llm():
    """Check the health of the LLM provider.

    Uses LLM_BACKEND and LLM_MODEL env vars. See docs/technical/LLM.md.
    """
    try:
        llm_config = get_llm_config()
        llm_provider = get_llm_provider_from_env()
        is_healthy = await llm_provider.health_check()
        if is_healthy:
            return JSONResponse(content={"status": "ok", "backend": llm_config.backend_model_pair})
        raise HTTPException(status_code=503, detail="LLM provider is not healthy.")
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"LLM config error: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM provider health check failed: {e}") from e


@router.get("/api/v1/health/vector")
async def health_vector_store():
    """Check the health of the vector store."""
    try:
        # Try to access the collection to verify it's working
        get_vector_store_manager()
        # This is a simple health check - we just verify we can create the manager
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vector store health check failed: {e}")


@router.get("/api/v1/health/auth")
async def health_auth():
    """Placeholder for auth service health check."""
    # In a microservices architecture, this would likely be a call to the auth service.
    # For now, we'll assume the auth service is healthy
    return JSONResponse(content={"status": "ok"})


@router.get("/api/v1/health/websocket")
async def health_websocket():
    """Placeholder for WebSocket health check."""
    # This might involve checking if the WebSocket manager is running.
    # For now, we'll assume the WebSocket is healthy
    return JSONResponse(content={"status": "ok"})
