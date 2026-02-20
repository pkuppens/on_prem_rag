"""Query service for semantic document search."""

from ..core.embeddings import query_embeddings
from ..core.vector_store import get_vector_store_manager
from ..utils.logging import StructuredLogger

logger = StructuredLogger(__name__)


class QueryService:
    """Service wrapping vector-store semantic search.

    Isolates routes from direct core imports, following the
    Routes → Services → Core → Storage architecture.
    """

    def __init__(self):
        self.vector_store_manager = get_vector_store_manager()

    def query(self, query_text: str, model_name: str, top_k: int) -> dict:
        """Run a semantic search against the vector store.

        Args:
            query_text: The search query.
            model_name: Embedding model name.
            top_k: Number of results to return.

        Returns:
            Dict of matching document chunks as returned by query_embeddings.
        """
        logger.debug("QueryService.query", query=query_text, top_k=top_k)
        return query_embeddings(
            query_text,
            model_name,
            persist_dir=self.vector_store_manager.config.persist_directory,
            collection_name=self.vector_store_manager.config.collection_name,
            top_k=top_k,
        )
