FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and update pip
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Install UV (external dependency)
RUN pip install --no-cache-dir uv

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy only the necessary files for installation
COPY pyproject.toml ./
COPY src ./src

# Install Python dependencies
RUN uv pip install --system -e .[dev] && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "rag_pipeline.file_ingestion:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
