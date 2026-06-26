"""Health check API endpoints for the Query Service.

Same URL paths as the original rag_pipeline/api/health.py for backward compatibility.
"""

from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from backend.rag_pipeline.config.llm_config import get_llm_config
from backend.rag_pipeline.core.llm_providers import get_llm_provider_from_env
from backend.rag_pipeline.core.vector_store import get_vector_store_manager

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
    try:
        get_vector_store_manager()
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")


@router.get("/api/v1/health/llm")
async def health_llm():
    """Check the health of the LLM provider."""
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
        get_vector_store_manager()
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vector store health check failed: {e}")


@router.get("/api/v1/health/auth")
async def health_auth():
    """Placeholder for auth service health check."""
    return JSONResponse(content={"status": "ok"})


@router.get("/api/v1/health/websocket")
async def health_websocket():
    """Placeholder for WebSocket health check."""
    return JSONResponse(content={"status": "ok"})
