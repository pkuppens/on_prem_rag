"""Query API endpoints for the Query Service.

Same URL paths as the original rag_pipeline/api/query.py for backward compatibility.
Provides endpoints for querying the document store using semantic search.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.rag_pipeline.config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from backend.rag_pipeline.utils.logging import StructuredLogger

from .metrics import get_metrics

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/v1/retrieval", tags=["retrieval"])

# Initialize QueryService from the old service location (will become a shim)
from backend.rag_pipeline.services.query_service import QueryService

query_service = QueryService()


class QueryRequest(BaseModel):
    """Payload for the query endpoint."""

    query: str
    params_name: str | None = None
    top_k: int | None = None


class ConversationRequest(BaseModel):
    """Payload for the conversation endpoint."""

    text: str


@router.post("/chunks")
async def query_documents(payload: QueryRequest) -> dict:
    """Return matching chunks for a query."""
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    params = get_param_set(payload.params_name or DEFAULT_PARAM_SET_NAME)
    top_k = payload.top_k if payload.top_k is not None else params.retrieval.top_k

    try:
        get_metrics().record_query()
        results = query_service.query(payload.query, params.embedding.model_name, top_k)
        return results
    except Exception as e:
        logger.error("Error during query", query=payload.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error during query: {str(e)}") from e


@router.post("/conversations")
async def process_conversation_endpoint(payload: ConversationRequest) -> dict:
    """Process a medical conversation through the RAG pipeline."""
    if not payload.text:
        raise HTTPException(status_code=400, detail="Text must not be empty")

    try:
        from backend.rag_pipeline.main import process_medical_conversation

        result = process_medical_conversation(payload.text)
        return {"result": result}
    except Exception as e:
        logger.error("Error during conversation processing", text=payload.text, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error during conversation processing: {str(e)}") from e
