# src/backend/rag_pipeline/api/health.py
import os

from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse

from ..core.llm_providers import LLMProviderFactory
from ..core.vector_store import get_vector_store_manager_from_env

router = APIRouter()


@router.get("/health")
async def health():
    """General health check endpoint for backward compatibility."""
    return JSONResponse(content={"status": "ok"})


@router.get("/api/health")
async def health_api():
    """Check the health of the API."""
    return JSONResponse(content={"status": "ok"})


@router.get("/api/health/database")
async def health_database():
    """Check the health of the database connection."""
    # For now, we'll assume the database is healthy since we're using ChromaDB
    # which doesn't require a separate database connection
    try:
        # Try to access the vector store to verify it's working
        get_vector_store_manager_from_env()
        # If we can create the vector store manager, the database is healthy
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")


@router.get("/api/health/llm")
async def health_llm():
    """Check the health of the LLM provider."""
    try:
        # Create a simple Ollama provider for health check.
        # Use OLLAMA_BASE_URL so it works in Docker (ollama:11434) and local (localhost:11434).
        ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        config = {"host": ollama_host}
        health_model = os.getenv("OLLAMA_MODEL", "mistral:7b")
        llm_provider = LLMProviderFactory.create_provider("ollama", health_model, config)
        is_healthy = await llm_provider.health_check()
        if is_healthy:
            return JSONResponse(content={"status": "ok"})
        else:
            raise HTTPException(status_code=503, detail="LLM provider is not healthy.")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM provider health check failed: {e}")


@router.get("/api/health/vector")
async def health_vector_store():
    """Check the health of the vector store."""
    try:
        # Try to access the collection to verify it's working
        get_vector_store_manager_from_env()
        # This is a simple health check - we just verify we can create the manager
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vector store health check failed: {e}")


@router.get("/api/health/auth")
async def health_auth():
    """Placeholder for auth service health check."""
    # In a microservices architecture, this would likely be a call to the auth service.
    # For now, we'll assume the auth service is healthy
    return JSONResponse(content={"status": "ok"})


@router.get("/api/health/websocket")
async def health_websocket():
    """Placeholder for WebSocket health check."""
    # This might involve checking if the WebSocket manager is running.
    # For now, we'll assume the WebSocket is healthy
    return JSONResponse(content={"status": "ok"})
