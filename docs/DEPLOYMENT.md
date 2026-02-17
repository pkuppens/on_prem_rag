# Production Deployment Guide

This document describes how to deploy the on_prem_rag application in a production-like environment.

## Prerequisites

- Docker and Docker Compose
- Ollama (for LLM inference) or compatible LLM backend
- Optional: OAuth2 credentials (Google, Microsoft) for authentication

## Port Configuration

The application uses a dedicated port range **9180-9199** to avoid conflicts with common development ports. See [docs/PORTS.md](PORTS.md) for details.

| Service  | Default Port | Description             |
| -------- | ------------ | ----------------------- |
| Backend  | 9180         | FastAPI RAG API         |
| Auth     | 9181         | OAuth2/JWT service      |
| ChromaDB | 9182         | Vector database         |
| Frontend | 5173         | React/Vite UI           |
| Ollama   | 11434        | LLM inference           |

Override any port via `.env` (copy from `env.example`).

## Build and Start

```bash
# 1. Copy environment template
cp env.example .env

# 2. Fill required values (OAuth secrets, SESSION_SECRET_KEY)
# Edit .env with your credentials

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify health
curl -s http://localhost:9180/health
curl -s http://localhost:9181/oauth/providers
curl -s http://localhost:9182/api/v2/heartbeat
```

## Health Checks

- **Backend**: `GET /health` returns `{"status": "healthy"}` when LLM and vector store are available
- **Auth**: `GET /oauth/providers` returns configured OAuth providers
- **ChromaDB**: `GET /api/v2/heartbeat` returns heartbeat

## Data Persistence

Data persists across container restarts via Docker named volumes:

| Volume       | Purpose                                      |
| ------------ | -------------------------------------------- |
| `chroma-data` | ChromaDB vector store (embeddings, metadata) |
| `ollama-data` | Ollama model cache                           |

Additional persistence:

- **uploaded_files/**: Uploaded document files (mounted from host)
- **data/chroma/**: Local Chroma persist directory (when running backend without Docker)

After ingestion, documents remain available after `docker-compose restart backend`. Verify with:

```bash
curl -s http://localhost:9180/api/documents/list
```

## Security Considerations

1. **Secrets**: Store `SESSION_SECRET_KEY`, `GOOGLE_CLIENT_SECRET`, `MICROSOFT_CLIENT_SECRET` securely (e.g. secrets manager, not in version control)
2. **OAuth redirect URIs**: Use production URLs in OAuth provider config (e.g. `https://yourdomain.com/oauth/google/callback`)
3. **Network exposure**: Bind backend/auth to internal network only; use reverse proxy (nginx, Traefik) for external access
4. **CORS**: Set `ALLOW_ORIGINS` to your frontend origin(s); avoid `*` in production

## Environment Variables

Key variables for production:

| Variable              | Purpose                          | Example                     |
| --------------------- | -------------------------------- | --------------------------- |
| `ENVIRONMENT`         | `development` or `production`    | `production`                |
| `OLLAMA_MODEL`        | LLM model name                   | `mistral:7b`                |
| `RETRIEVAL_STRATEGY`  | Default retrieval strategy       | `dense`, `sparse`, `hybrid` |
| `SESSION_SECRET_KEY`  | Session signing key             | (random, 32+ chars)         |
| `ALLOW_ORIGINS`       | CORS allowed origins             | `https://yourdomain.com`    |

See `env.example` for full list.

## Stopping and Cleanup

```bash
# Stop containers (preserves volumes)
docker-compose down

# Stop and remove volumes (deletes ChromaDB data, Ollama cache)
docker-compose down -v
```

## Related Documentation

- [docs/TEST_DOCKER.md](TEST_DOCKER.md) — Docker development and testing
- [docs/PORTS.md](PORTS.md) — Port configuration and conflict resolution
- [docs/USAGE.md](USAGE.md) — Using the application and API
