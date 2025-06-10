# Docker Technical Documentation

## Architecture Overview

### Container Structure

```
on_prem_rag/
├── backend/          # FastAPI application
├── frontend/         # Vite frontend
├── chroma/           # Vector database
└── auth/            # Authentication service
```

### Network Architecture

- All services connected via `app-network` bridge network
- Host machine accessible via `host.docker.internal`
- Port mappings for external access

## Build Process

### Layer Optimization

1. **Base Image Selection**:

   - Backend: `python:3.12-slim`
   - Frontend: `node:18-alpine`
   - ChromaDB: Official image

2. **Layer Caching Strategy**:

   ```dockerfile
   # System dependencies (cached)
   RUN apt-get update && apt-get install -y ...

   # Application dependencies (cached if unchanged)
   COPY pyproject.toml ./
   RUN pip install ...

   # Application code (changes frequently)
   COPY src ./src
   ```

3. **Multi-stage Builds**:
   - Consider for production builds
   - Separate build and runtime stages
   - Reduce final image size

### Volume Management

1. **Named Volumes**:

   - `chroma-data`: Persists vector database
   - `node_modules`: Isolates frontend dependencies

2. **Bind Mounts**:
   - Source code for hot reloading
   - Test data and uploaded files
   - Configuration files

## Development Workflow

### Local Development

1. **Start Development Environment**:

   ```bash
   # Initial setup
   docker-compose up --build

   # Subsequent starts
   docker-compose up
   ```

2. **Code Changes**:

   - Backend: Hot reload via uvicorn
   - Frontend: Vite dev server
   - No rebuild needed for most changes

3. **Dependency Updates**:
   ```bash
   # After changing dependencies
   docker-compose build backend frontend
   ```

### Testing

1. **Unit Tests**:

   ```bash
   docker-compose exec backend pytest
   ```

2. **Integration Tests**:

   ```bash
   docker-compose exec backend pytest tests/integration
   ```

3. **End-to-End Tests**:
   ```bash
   docker-compose exec frontend npm run test:e2e
   ```

## Performance Optimization

### Build Performance

1. **Use .dockerignore**:

   - Exclude unnecessary files
   - Reduce build context size
   - Speed up build process

2. **Layer Caching**:

   - Order commands from least to most frequently changed
   - Combine related commands
   - Use multi-stage builds

3. **Dependency Management**:
   - Pin dependency versions
   - Use requirements.txt or pyproject.toml
   - Consider using dependency caching

### Runtime Performance

1. **Resource Limits**:

   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: "1"
             memory: 1G
   ```

2. **Volume Performance**:
   - Use named volumes for databases
   - Bind mounts for development
   - Consider volume caching options

## Security Considerations

1. **Non-root Users**:

   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

2. **Network Security**:

   - Use internal networks
   - Limit exposed ports
   - Implement proper CORS

3. **Secret Management**:
   - Use environment variables
   - Consider Docker secrets
   - Never commit secrets

## Monitoring and Debugging

1. **Container Logs**:

   ```bash
   docker-compose logs -f
   ```

2. **Resource Usage**:

   ```bash
   docker stats
   ```

3. **Container Inspection**:
   ```bash
   docker-compose exec backend sh
   ```

## Common Issues and Solutions

1. **Port Conflicts**:

   - Check running services
   - Use different port ranges
   - Update configuration

2. **Volume Issues**:

   - Check permissions
   - Verify mount points
   - Clear volumes if needed

3. **Network Problems**:
   - Check network configuration
   - Verify service discovery
   - Test connectivity

## Best Practices

1. **Image Management**:

   - Regular cleanup of unused images
   - Version tagging
   - Security scanning

2. **Development Workflow**:

   - Use docker-compose for consistency
   - Implement proper testing
   - Document changes

3. **Production Considerations**:
   - Use production-specific compose file
   - Implement health checks
   - Set up monitoring

## Maintenance

1. **Regular Updates**:

   ```bash
   docker-compose pull
   docker-compose build
   ```

2. **Cleanup**:

   ```bash
   docker system prune
   docker volume prune
   ```

3. **Backup**:
   ```bash
   docker-compose down
   tar -czf volumes.tar.gz $(docker volume ls -q)
   ```
