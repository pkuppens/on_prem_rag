# Port Configuration

This document describes the port configuration for both local development and Docker environments.

## Dedicated Port Range (Conflict Avoidance)

To avoid conflicts with common development ports (8000, 8080, 9000, etc.), this application uses a dedicated range **9180-9199**:

| Service  | Default | Description             | Override Variable     |
| -------- | ------- | ----------------------- | -------------------- |
| Backend  | 9180    | FastAPI application     | `BACKEND_PORT`        |
| Auth     | 9181    | Authentication service  | `AUTH_PORT`           |
| ChromaDB | 9182    | Vector database (host)  | `CHROMA_HOST_PORT`    |
| Frontend | 5173    | Vite development server | `FRONTEND_PORT`       |
| Ollama   | 11434   | LLM service (host)      | `OLLAMA_HOST_PORT`    |

Ports are configurable via `.env`. Override any value if it conflicts with other services on your machine. See `env.example` and [TEST_DOCKER.md](TEST_DOCKER.md#port-conflicts).

## Configuration

### Backend

- Internal/external port: 9180 (default)
- Environment variable: `PORT=9180` or `BACKEND_PORT=9180`
- Override: `BACKEND_PORT` in `.env`

### Auth Service

- Internal/external port: 9181 (default)
- Environment variable: `PORT=9181` or `AUTH_PORT=9181`
- Override: `AUTH_PORT` in `.env`

### ChromaDB

- Internal port: 8000 (fixed by ChromaDB)
- External port: 9182 (default)
- Override: `CHROMA_HOST_PORT` in `.env`

### Frontend

- Internal port: 5173
- External port: 5173
- Environment variables (set by docker-compose from BACKEND_PORT, AUTH_PORT):
  - `VITE_BACKEND_URL=http://localhost:9180`
  - `VITE_AUTH_URL=http://localhost:9181`

### Ollama

- Port: 11434 (default)
- Access: `host.docker.internal:11434`
- Environment variable: `OLLAMA_BASE_URL=http://host.docker.internal:11434`

## Docker Configuration

Ports in `docker-compose.yml` use env vars with defaults in the 9180-9199 range. Override in `.env`:

```yaml
# docker-compose.yml defaults:
# BACKEND_PORT:-9180, AUTH_PORT:-9181, CHROMA_HOST_PORT:-9182,
# OLLAMA_HOST_PORT:-11434, FRONTEND_PORT:-5173
```

## Local Development

For local development without Docker:

1. Backend runs on port 9180 (or BACKEND_PORT)
2. Auth service runs on port 9181 (or AUTH_PORT)
3. ChromaDB runs on port 9182 (or CHROMA_HOST_PORT)
4. Frontend runs on port 5173
5. Ollama runs on port 11434

## Port Range Selection

We use a dedicated range **9180-9199** to avoid conflicts with common ports:

- **9180**: Backend (avoids 8000, 8080, 9000)
- **9181**: Auth service
- **9182**: ChromaDB host mapping
- **5173**: Frontend (Vite default)
- **11434**: Ollama (upstream default)

This scheme:

1. Avoids conflicts with common development ports (3000-9000)
2. Groups application services in one contiguous range
3. Allows override via `.env` for any port
4. Makes it clear these are on_prem_rag ports

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
