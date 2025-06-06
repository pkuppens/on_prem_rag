import asyncio
import hashlib
import inspect
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from rag_pipeline.config.parameter_sets import (
    DEFAULT_PARAM_SET_NAME,
    available_param_sets,
    get_param_set,
)
from rag_pipeline.core.document_loader import DocumentLoader
from rag_pipeline.core.vector_store import get_vector_store_manager_from_env


# Set up structured logging
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

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


logger = StructuredLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store upload progress
upload_progress: dict[str, float] = {}

# Global helpers
document_loader = DocumentLoader()
vector_store_manager = get_vector_store_manager_from_env()
chunk_hashes: set[str] = set()


@app.get("/api/parameters/sets")
async def get_parameter_sets() -> dict:
    """Return available RAG parameter sets and default selection."""

    return {"default": DEFAULT_PARAM_SET_NAME, "sets": available_param_sets()}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile, params_name: str = DEFAULT_PARAM_SET_NAME):
    """Handle file upload, chunking, and embedding."""

    try:
        logger.info("Received file upload", filename=file.filename, size=file.size, content_type=file.content_type)

        params = get_param_set(params_name)

        # Save upload to a temporary location
        temp_dir = Path("uploaded_files")
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Load document using loader with duplicate detection
        documents, _ = document_loader.load_document(file_path)
        if not documents:
            upload_progress[file.filename] = 100
            return {"message": "Duplicate file", "filename": file.filename}

        parser = SimpleNodeParser.from_defaults(
            chunk_size=params.chunking.chunk_size,
            chunk_overlap=params.chunking.chunk_overlap,
            include_metadata=True,
        )
        nodes = parser.get_nodes_from_documents(documents)

        unique_nodes = []
        for node in nodes:
            chunk_hash = hashlib.sha256(node.text.encode("utf-8")).hexdigest()
            if chunk_hash in chunk_hashes:
                continue
            chunk_hashes.add(chunk_hash)
            node.metadata["chunk_hash"] = chunk_hash
            unique_nodes.append(node)

        embed_model = HuggingFaceEmbedding(
            model_name=params.embedding.model_name,
            cache_folder="cache/embeddings",
        )

        total = len(unique_nodes)
        for idx, node in enumerate(unique_nodes, start=1):
            embedding = embed_model.get_text_embedding(node.text)
            vector_store_manager.add_embeddings(
                ids=[node.node_id],
                embeddings=[embedding],
                metadatas=[node.metadata],
            )
            upload_progress[file.filename] = int(idx / total * 100)

        upload_progress[file.filename] = 100
        logger.info("File processing completed", filename=file.filename, chunks=total)
        return {"message": "File processed successfully", "filename": file.filename, "chunks": total}

    except Exception as e:  # pragma: no cover - runtime errors reported during manual runs
        logger.error("Error processing file", filename=file.filename, error=str(e))
        raise


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
