import asyncio
import inspect
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware


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


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile):
    """Handle file upload and process document."""
    try:
        # Log file metadata
        logger.info("Received file upload", filename=file.filename, size=file.size, content_type=file.content_type)

        # Simulate processing with progress updates
        for progress in range(0, 101, 20):
            upload_progress[file.filename] = progress
            logger.debug("Processing progress update", filename=file.filename, progress=progress)
            await asyncio.sleep(1)

        logger.info("File processing completed", filename=file.filename)
        return {"message": "File processed successfully", "filename": file.filename}

    except Exception as e:
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
