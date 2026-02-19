# Multi-stage build: builder + runtime for smaller final image.
# Builder installs deps (including build-essential); runtime excludes build tools.
# See docs/DOCKER_TECHNICAL.md and docs/TEST_DOCKER.md for build and deployment details.

# -----------------------------------------------------------------------------
# Builder stage: install dependencies and build native extensions
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml ./
COPY src ./src

RUN uv pip install --system -e .[dev]

# -----------------------------------------------------------------------------
# Runtime stage: minimal image, no build-essential
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install curl for healthchecks, util-linux for runuser (entrypoint)
RUN apt-get update && apt-get install -y --no-install-recommends curl util-linux \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

# Copy installed packages and app from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN chown -R appuser:appuser /app

COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

ENV PYTHONPATH=/app:/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command (overridden by docker-compose for backend/auth)
CMD ["uvicorn", "backend.rag_pipeline.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
