# Testing in Docker

This document explains how to run tests and use the application in the Docker development environment.

## Verification Checklist

**Prerequisite:** Docker Desktop (or Docker Engine) must be running. If commands fail with "error during connect" or "cannot find the file specified", start Docker Desktop and wait until it is ready.

Run these steps to verify containers build and provide services correctly:

```bash
# 1. Build all images
docker-compose build

# 2. Start services (detached)
docker-compose up -d

# 3. Wait for health checks (chroma, backend, auth)
# Then check status — chroma, backend, auth should show "healthy"
docker-compose ps

# 4. Verify endpoints
curl -s http://localhost:9180/health
curl -s http://localhost:9181/oauth/providers
curl -s http://localhost:9182/api/v2/heartbeat

# 5. Verify STT (voice pipeline) — device should be "cpu" in Docker
curl -s http://localhost:9180/api/stt/info | python -m json.tool

# 6. Stop
docker-compose down
```

If Chroma is on a different port (see `CHROMA_HOST_PORT` in `env.example`), adjust the heartbeat URL accordingly.

## Docker Management Commands

### Building Images

1. **Initial Build** (with layer caching):

   ```bash
   docker-compose build
   ```

2. **Force Rebuild** (ignore cache):

   ```bash
   docker-compose build --no-cache
   ```

3. **Rebuild Specific Service**:

   ```bash
   docker-compose build backend
   ```

4. **Build with Progress**:
   ```bash
   docker-compose build --progress=plain
   ```

### Managing Containers

1. **Start Services**:

   ```bash
   docker-compose up        # Attached mode
   docker-compose up -d     # Detached mode
   ```

2. **Stop Services**:

   ```bash
   docker-compose down     # Stop and remove containers
   docker-compose stop     # Stop without removing
   ```

3. **View Logs**:

   ```bash
   docker-compose logs     # All services
   docker-compose logs -f  # Follow mode
   docker-compose logs backend  # Specific service
   ```

   **Ingestion timing**: To trace document processing bottlenecks (load, chunk, embed model load, embed gen, store):

   ```bash
   docker logs on_prem_rag-backend-1 2>&1 | grep INGEST
   ```

   Logs include `INGEST: PDF load start`, `INGEST: PDF load done`, `INGEST: model load start`, `INGEST: model load done`, `chunk_done`, `embed_gen_done`, `store_done`, `total_done`, each with `elapsed_ms` where applicable.

4. **Clean Up**:
   ```bash
   docker-compose down     # Stop and remove containers (keeps named volumes)
   docker-compose down -v  # Also remove named volumes (chroma-data, ollama-data, frontend-node-modules)
   docker volume prune    # Remove orphaned volumes from previous anonymous mounts
   docker system prune    # Remove unused images, networks
   ```

   **Named volumes** (`chroma-data`, `ollama-data`, `frontend-node-modules`) persist between sessions and are reused on `docker-compose up`. Orphaned anonymous volumes can be removed with `docker volume prune`.

### Development Workflow

1. **Start Development Environment**:

   ```bash
   # First time or after changes
   docker-compose up --build

   # Subsequent starts
   docker-compose up
   ```

2. **Rebuild After Dependencies Change**:

   ```bash
   # After changing pyproject.toml or package.json
   docker-compose build backend frontend
   docker-compose up
   ```

3. **Hot Reload Development**:

   ```bash
   # Start with hot reload
   docker-compose up

   # In another terminal, rebuild specific service
   docker-compose build backend
   ```

## Running Tests

### Running Tests Inside the Container

To run all tests inside the backend container:

```bash
docker-compose exec backend pytest
```

For specific test files or directories:

```bash
docker-compose exec backend pytest tests/path/to/test_file.py
```

### Running Tests with Coverage

```bash
docker-compose exec backend pytest --cov=src tests/
```

### Ollama Integration Tests (local LLM)

Tests marked `@pytest.mark.ollama` require Ollama (local LLM on port 11434). They are excluded from default CI. No Docker needed — just `ollama serve` plus `uv run start-backend`.

1. Start Ollama: `ollama serve` (and `ollama pull mistral` if needed).
2. Start backend: `uv run start-backend`.
3. Run: `uv run pytest -m ollama -v`.

If Ollama is not running, these tests skip with: *"Ollama (LLM service) not running on port 11434. Start with: ollama serve."*

### Docker Deployment Tests

Tests marked `@pytest.mark.docker` require the full Docker stack (backend, auth, frontend, etc.). Use `docker-compose up -d` and run against the deployed services. For deployment validation.

### Test Docker Build Process

1. **Test Initial Build**:

   ```bash
   # Clean start
   docker-compose down -v
   docker system prune -f
   docker-compose build --no-cache
   ```

2. **Test Cached Build**:

   ```bash
   # Should use cached layers
   docker-compose build
   ```

3. **Test Service Rebuild**:

   ```bash
   # After changing backend code
   docker-compose build backend
   ```

4. **Test Volume Mounts**:
   ```bash
   # Verify mounted directories
   docker-compose exec backend ls /app/src
   docker-compose exec backend ls /app/tests
   ```

## Data Persistence

The following data is persisted between container restarts:

- ChromaDB data: Stored in the `chroma-data` Docker volume
- Uploaded files: Stored in the `uploaded-files-data` named volume (mounted at `/app/uploaded_files` in backend)
- Test data: Stored in the `./test_data` directory

## Hot Reloading

The application supports hot reloading:

- Backend: Changes to Python files in `src/` will trigger automatic reload
- Frontend: Changes to files in `src/frontend/` will trigger automatic reload

## Important Directories

The following directories are mounted into the containers:

- `./src`: Backend source code
- `./tests`: Test files
- `./test_data`: Test data files
- `uploaded-files-data` (named volume): User uploaded files at `/app/uploaded_files`
- `./src/frontend`: Frontend source code

## Environment Variables

The backend service uses `env_file: .env`, so variables like `STT_MODEL_SIZE=turbo` from `.env` are passed to the container. Ensure `.env` exists and contains your desired STT model.

Key environment variables (set in `.env` or `env.example`):

**Port overrides** (Docker Compose):

- `BACKEND_PORT`, `AUTH_PORT`, `CHROMA_HOST_PORT`, `OLLAMA_HOST_PORT`, `FRONTEND_PORT`

**Service config**:

- `CHROMA_HOST`: ChromaDB service hostname (default: chroma)
- `CHROMA_PORT`: ChromaDB internal port (8000)
- `ALLOW_ORIGINS`: CORS allowed origins
- `ENVIRONMENT`: Set to 'development' for local development
- `VITE_BACKEND_URL`: Frontend backend API URL (must match `BACKEND_PORT`)
- `OLLAMA_BASE_URL`: Ollama URL; default http://ollama:11434 (Docker). Set to `http://host.docker.internal:11434` for host Ollama reuse; then start without ollama service.

## Port Conflicts

When `docker-compose up` fails with "port is already allocated" or "address already in use":

1. **Identify the conflicting port** from the error message (e.g. 9100, 11434).
2. **Override in `.env`** — copy `env.example` to `.env` if needed, then set:
   - `BACKEND_PORT=9190` (if 9180 is in use)
   - `AUTH_PORT=9191` (if 9181 is in use)
   - `CHROMA_HOST_PORT=9192` (if 9182 is in use)
   - `OLLAMA_HOST_PORT=11435` (if host Ollama uses 11434)
   - `FRONTEND_PORT=5180` (if 5173 is in use)
3. **Restart**: `docker-compose down` then `docker-compose up`.

**Common conflicts:**

- Defaults use dedicated range 9180-9182 (see docs/PORTS.md).
- **Reuse host Ollama** — Set `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` and start with `docker-compose up -d chroma backend auth frontend` (omit ollama service).
- **Ollama on host** (port 11434) — If also running Docker ollama, set `OLLAMA_HOST_PORT=11435` so Docker ollama uses a different port.
- **Frontend port 5173 in use** — Create `.env` with `FRONTEND_PORT=5180` (or another free port).
- Multiple dev stacks — assign unique ports per project in `.env`.

## Troubleshooting

If you encounter issues:

1. **Docker daemon not running** — If `docker-compose build` or `docker-compose up` fails with "error during connect", "cannot find the file specified", or "Cannot connect to the Docker daemon":

   - **Windows/macOS**: Start **Docker Desktop** and wait until it reports "Docker Engine running".
   - **Linux**: Run `sudo systemctl start docker` (or your distro's equivalent).

2. Check container logs:

   ```bash
   docker-compose logs backend
   ```

3. Rebuild containers:

   ```bash
   docker-compose build
   ```

4. Reset volumes (warning: this will delete all data):

   ```bash
   docker-compose down -v
   docker-compose up
   ```

5. Check container status and health:

   ```bash
   docker-compose ps
   ```

   Unhealthy services show `unhealthy` in the status — check logs for that service.

6. Inspect container:

   ```bash
   docker-compose exec backend sh
   ```

7. Check network connectivity:
   ```bash
   docker network inspect on_prem_rag_app-network
   ```
