# Port Configuration

This document describes the port configuration for both local development and Docker environments.

## Port Assignments

| Service  | Default | Description             | Override Variable     |
| -------- | ------- | ----------------------- | -------------------- |
| Backend  | 9000    | FastAPI application     | `BACKEND_PORT`        |
| Auth     | 9100    | Authentication service  | `AUTH_PORT`           |
| ChromaDB | 9200    | Vector database (host)  | `CHROMA_HOST_PORT`    |
| Frontend | 5173    | Vite development server | `FRONTEND_PORT`       |
| Ollama   | 11434   | LLM service (host)      | `OLLAMA_HOST_PORT`    |

Ports are configurable via `.env` to avoid conflicts. See `env.example` and [TEST_DOCKER.md](TEST_DOCKER.md#port-conflicts).

## Configuration

### Backend

- Internal port: 9000
- External port: 9000
- Environment variable: `PORT=9000`

### Auth Service

- Internal port: 9100
- External port: 9100
- Environment variable: `PORT=9100`

### ChromaDB

- Internal port: 8000 (fixed by ChromaDB)
- External port: 9200 (default; was 9100, changed to avoid conflict with Auth)
- Override: `CHROMA_HOST_PORT` in `.env`

### Frontend

- Internal port: 5173
- External port: 5173
- Environment variables:
  - `VITE_BACKEND_URL=http://localhost:9000`
  - `VITE_AUTH_URL=http://localhost:9100`

### Ollama

- Port: 11434 (default)
- Access: `host.docker.internal:11434`
- Environment variable: `OLLAMA_BASE_URL=http://host.docker.internal:11434`

## Docker Configuration

Ports in `docker-compose.yml` use env vars (e.g. `${BACKEND_PORT:-9000}`). Override in `.env`:

```yaml
# docker-compose.yml uses:
# BACKEND_PORT:-9000, AUTH_PORT:-9100, CHROMA_HOST_PORT:-9200,
# OLLAMA_HOST_PORT:-11434, FRONTEND_PORT:-5173
```

## Local Development

For local development without Docker:

1. Backend runs on port 9000
2. Auth service runs on port 9100
3. ChromaDB runs on port 9100
4. Frontend runs on port 5173
5. Ollama runs on port 11434

## Port Range Selection

We use the following port ranges:

- 9000-9099: Core application services
- 9100-9199: Supporting services
- 5173: Frontend (Vite default)

This scheme:

1. Avoids conflicts with common development ports (3000-8000)
2. Groups related services together
3. Allows for future service additions
4. Makes it clear these are our application ports

## Ollama Integration

**Full Docker stack**: Ollama runs as a service in docker-compose. Backend uses `http://ollama:11434`.

**Host Ollama** (optional): If Ollama runs on the host, set `OLLAMA_BASE_URL=http://host.docker.internal:11434` and ensure `extra_hosts` is configured. Override port with `OLLAMA_HOST_PORT` if host Ollama uses a different port.

## Troubleshooting

If you encounter port conflicts:

1. Check if any service is already using the required ports
2. Verify the port mappings in docker-compose.yml
3. Ensure environment variables are set correctly
4. Check service logs for port-related errors
5. Consider using a different port in the appropriate range if needed

For Ollama issues:

1. Verify Ollama is running on the host
2. Check if port 11434 is accessible
3. Verify `host.docker.internal` is working
4. Check network connectivity between container and host
