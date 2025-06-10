# Testing in Docker

This document explains how to run tests and use the application in the Docker development environment.

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

4. **Clean Up**:
   ```bash
   docker-compose down -v  # Remove containers and volumes
   docker system prune     # Remove unused images, networks
   ```

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
- Uploaded files: Stored in the `./uploaded_files` directory
- Test data: Stored in the `./test_data` directory

## Hot Reloading

The application supports hot reloading:

- Backend: Changes to Python files in `src/` will trigger automatic reload
- Frontend: Changes to files in `frontend/` will trigger automatic reload

## Important Directories

The following directories are mounted into the containers:

- `./src`: Backend source code
- `./tests`: Test files
- `./test_data`: Test data files
- `./uploaded_files`: User uploaded files
- `./frontend`: Frontend source code

## Environment Variables

Key environment variables used in development:

- `CHROMA_HOST`: ChromaDB service hostname
- `CHROMA_PORT`: ChromaDB service port
- `ALLOW_ORIGINS`: CORS allowed origins
- `ENVIRONMENT`: Set to 'development' for local development
- `VITE_BACKEND_URL`: Frontend backend API URL
- `OLLAMA_BASE_URL`: URL for local Ollama instance

## Troubleshooting

If you encounter issues:

1. Check container logs:

   ```bash
   docker-compose logs backend
   ```

2. Rebuild containers:

   ```bash
   docker-compose build
   ```

3. Reset volumes (warning: this will delete all data):

   ```bash
   docker-compose down -v
   docker-compose up
   ```

4. Check container status:

   ```bash
   docker-compose ps
   ```

5. Inspect container:

   ```bash
   docker-compose exec backend sh
   ```

6. Check network connectivity:
   ```bash
   docker network inspect on_prem_rag_app-network
   ```
