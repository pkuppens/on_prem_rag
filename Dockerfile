FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv
RUN uv pip install -e .
COPY src ./src
CMD ["uvicorn", "rag_pipeline.file_ingestion:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
