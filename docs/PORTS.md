# Port Configuration

This document describes the port configuration for both local development and Docker environments.

## Port Assignments

| Service  | Port  | Description             | Environment Variable |
| -------- | ----- | ----------------------- | -------------------- |
| Backend  | 9000  | FastAPI application     | PORT                 |
| Auth     | 9100  | Authentication service  | PORT                 |
| ChromaDB | 9100  | Vector database API     | CHROMA_PORT          |
| Frontend | 5173  | Vite development server | VITE_PORT            |
| Ollama   | 11434 | Local LLM service       | OLLAMA_BASE_URL      |

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
- External port: 9100
- Environment variable: `CHROMA_PORT=8000` (internal)

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

In `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "9000:9000" # Backend API
    extra_hosts:
      - "host.docker.internal:host-gateway" # For Ollama access
  auth:
    ports:
      - "9100:9100" # Auth service
  chroma:
    ports:
      - "9100:8000" # ChromaDB API
  frontend:
    ports:
      - "5173:5173" # Frontend dev server
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

The application is configured to use the host's Ollama instance:

- Uses `host.docker.internal` to access the host machine
- Requires `extra_hosts` configuration in Docker
- Assumes Ollama is running on the default port (11434)

Benefits:

- Reuses existing Ollama instance
- Saves resources
- Maintains model consistency

Considerations:

- Requires Ollama to be running on the host
- Less isolated environment
- May need version compatibility checks

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
