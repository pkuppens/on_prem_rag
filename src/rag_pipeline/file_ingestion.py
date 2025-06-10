import asyncio
import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pydantic import BaseModel

from rag_pipeline.config.parameter_sets import (
    DEFAULT_PARAM_SET_NAME,
    available_param_sets,
    get_param_set,
)
from rag_pipeline.core.document_loader import DocumentLoader
from rag_pipeline.core.embeddings import query_embeddings
from rag_pipeline.core.vector_store import get_vector_store_manager_from_env
from rag_pipeline.utils.directory_utils import get_uploaded_files_dir

NODES_PER_YIELD = 1  # Yield control to event loop every N nodes to allow WebSocket and UI updates


# Set up structured logging
class StructuredLogger:
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.level = level

        # Create console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(levelname)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _get_caller_info(self):
        frame = inspect.currentframe().f_back.f_back
        return {"filename": Path(frame.f_code.co_filename).name, "function": frame.f_code.co_name, "line": frame.f_lineno}

    def info(self, message: str, **kwargs):
        caller = self._get_caller_info()
        self.logger.info(f"{message} | {json.dumps({**caller, **kwargs})}")

    def error(self, message: str, **kwargs):
        caller = self._get_caller_info()
        self.logger.error(f"{message} | {json.dumps({**caller, **kwargs})}")

    def debug(self, message: str, **kwargs):
        caller = self._get_caller_info()
        self.logger.debug(f"{message} | {json.dumps({**caller, **kwargs})}")


logger = StructuredLogger(__name__, level=logging.DEBUG)

# Ensure uploaded_files directory exists
uploaded_files_dir = get_uploaded_files_dir()
uploaded_files_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.mount("/files", StaticFiles(directory=str(uploaded_files_dir)), name="files")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store upload progress
upload_progress: dict[str, int] = {}

# Global helpers
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager_from_env()
chunk_hashes: set[str] = set()


class QueryRequest(BaseModel):
    """Payload for the query endpoint."""

    query: str
    params_name: str | None = None
    top_k: int | None = None  # Optional override for number of results


@app.get("/api/parameters/sets")
async def get_parameter_sets() -> dict:
    """Return available RAG parameter sets and default selection."""
    logger.info("GET /api/parameters/sets")

    return {"default": DEFAULT_PARAM_SET_NAME, "sets": available_param_sets()}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile, params_name: str = DEFAULT_PARAM_SET_NAME):
    """Handle file upload, chunking, and embedding."""

    try:
        logger.info("POST /api/documents/upload", filename=file.filename, size=file.size, content_type=file.content_type)

        params = get_param_set(params_name)  # from dictionary, not the GET function call

        # Save upload to a temporary location
        temp_dir = Path("uploaded_files")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
            logger.debug("File saved to", filename=str(file_path))
            upload_progress[file.filename] = 10

        # Load document using loader with duplicate detection
        documents, _ = document_loader.load_document(file_path)
        if not documents:
            logger.debug("No documents found in file", filename=str(file_path))
            upload_progress[file.filename] = 100
            return {"message": "Duplicate file", "filename": file.filename}

        parser = SimpleNodeParser.from_defaults(
            chunk_size=params.chunking.chunk_size,
            chunk_overlap=params.chunking.chunk_overlap,
            include_metadata=True,
        )
        nodes = parser.get_nodes_from_documents(documents)
        total_nodes = len(nodes)
        logger.debug("Nodes parsed", filename=str(file_path), total_nodes=total_nodes)
        upload_progress[file.filename] = 15

        unique_nodes = []
        for node in nodes:
            chunk_hash = hashlib.sha256(node.text.encode("utf-8")).hexdigest()
            if chunk_hash in chunk_hashes:
                continue
            chunk_hashes.add(chunk_hash)
            # Store the hash in the node for later use
            node.metadata["chunk_hash"] = chunk_hash
            unique_nodes.append(node)

        embed_model = HuggingFaceEmbedding(
            model_name=params.embedding.model_name,
            cache_folder="cache/embeddings",
        )

        total = len(unique_nodes)
        for idx, node in enumerate(unique_nodes, start=1):
            embedding = embed_model.get_text_embedding(node.text)

            # Enhanced metadata with required fields for query results
            enhanced_metadata = {
                **node.metadata,  # Keep existing metadata (includes chunk_hash)
                "text": node.text,
                "document_name": file.filename,
                "document_id": f"{file_path.stem}_{idx - 1}",  # Generate stable document ID
                "chunk_index": idx - 1,
                "page_number": node.metadata.get("page_label", "unknown"),
                "source": str(file_path),
            }

            vector_store_manager.add_embeddings(
                ids=[node.node_id],
                embeddings=[embedding],
                metadatas=[enhanced_metadata],
            )
            upload_progress[file.filename] = 15 + int(80 * idx / total)
            # Yield control to event loop every NODES_PER_YIELD nodes to allow WebSocket updates
            # Can be just 1 because the WebSocket updates are not that frequent and rendering fast
            if idx % NODES_PER_YIELD == 0:
                await asyncio.sleep(0)

        upload_progress[file.filename] = 100  # upload completed
        logger.info("File processing completed", filename=file.filename, chunks=total)
        return {"message": "File processed successfully", "filename": file.filename, "chunks": total}

    except Exception as e:  # pragma: no cover - runtime errors reported during manual runs
        logger.error("Error processing file", filename=file.filename, error=str(e))
        raise


@app.post("/api/query")
async def query_documents(payload: QueryRequest) -> dict:
    """Return matching chunks for a query."""

    if not payload.query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    params = get_param_set(payload.params_name or DEFAULT_PARAM_SET_NAME)

    # Use custom top_k if provided, otherwise use parameter set default
    top_k = payload.top_k if payload.top_k is not None else params.retrieval.top_k

    results = query_embeddings(
        payload.query,
        params.embedding.model_name,
        persist_dir=vector_store_manager.config.persist_directory,
        collection_name=vector_store_manager.config.collection_name,
        top_k=top_k,
    )
    return results


@app.websocket("/ws/upload-progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Send current progress for all files
            await websocket.send_json(upload_progress)
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
    finally:
        logger.info("WebSocket connection closed")
        await websocket.close()


def start_server():
    """Entry point for starting the backend server."""
    import uvicorn

    logger.info("Starting backend server")
    uvicorn.run("rag_pipeline.file_ingestion:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start_server()
