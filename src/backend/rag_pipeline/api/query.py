"""Query API endpoints for the RAG pipeline.

This module provides endpoints for querying the document store
using semantic search.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config.parameter_sets import DEFAULT_PARAM_SET_NAME, get_param_set
from ..core.embeddings import query_embeddings
from ..core.vector_store import get_vector_store_manager_from_env
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["query"])

# Initialize services
vector_store_manager = get_vector_store_manager_from_env()


class QueryRequest(BaseModel):
    """Payload for the query endpoint.

    Attributes:
        query: The search query text
        params_name: Optional name of parameter set to use
        top_k: Optional override for number of results
    """

    query: str
    params_name: str | None = None
    top_k: int | None = None


@router.post("")
async def query_documents(payload: QueryRequest) -> dict:
    """Return matching chunks for a query.

    Args:
        payload: The query request containing search text and options

    Returns:
        Dict containing matching document chunks

    Raises:
        HTTPException: If query is empty or search fails
    """
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    params = get_param_set(payload.params_name or DEFAULT_PARAM_SET_NAME)

    # Use custom top_k if provided, otherwise use parameter set default
    top_k = payload.top_k if payload.top_k is not None else params.retrieval.top_k

    try:
        results = query_embeddings(
            payload.query,
            params.embedding.model_name,
            persist_dir=vector_store_manager.config.persist_directory,
            collection_name=vector_store_manager.config.collection_name,
            top_k=top_k,
        )
        return results
    except Exception as e:
        logger.error("Error during query", query=payload.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error during query: {str(e)}") from e
