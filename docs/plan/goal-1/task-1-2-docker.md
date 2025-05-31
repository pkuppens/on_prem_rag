# Task 1.2: Containerized Environment

## Context from Goal 1

This task establishes the containerized deployment foundation for our on-premises RAG solution. The Docker environment must ensure consistent deployment across different environments while enabling easy scaling and service isolation for enterprise deployment.

## Problem Statement

We need a robust containerized environment that:
- Provides consistent deployment across development, staging, and production
- Isolates services for security and maintainability
- Supports both development workflows and production deployment
- Enables easy scaling of individual components

## Technology Considerations

### Container Orchestration Options

#### Option 1: Docker Compose (Chosen)
- **Pros**: Simple, great for single-host deployment, excellent for development
- **Cons**: Limited scaling capabilities, single-host limitation
- **Use Case**: Development, small-scale production, proof-of-concept

#### Option 2: Kubernetes
- **Pros**: Enterprise-grade scaling, advanced features, cloud-native
- **Cons**: Complex setup, overkill for single-host deployment
- **Use Case**: Large-scale production, multi-host deployments

#### Option 3: Docker Swarm
- **Pros**: Native Docker orchestration, simpler than Kubernetes
- **Cons**: Less ecosystem support, limited advanced features
- **Use Case**: Medium-scale production deployments

### Decision: Docker Compose + Migration Path

**Rationale**: Start with Docker Compose for simplicity and development speed. Design containers to be Kubernetes-ready for future migration if scaling requirements emerge.

## Service Architecture

```mermaid
graph TB
    A[nginx - Reverse Proxy] --> B[api - FastAPI Backend]
    A --> C[frontend - Streamlit/React UI]
    B --> D[vectordb - ChromaDB]
    B --> E[ollama - Local LLM]
    F[redis - Cache/Session] --> B
    G[postgres - User/Metadata] --> B
    
    subgraph "Data Volumes"
        H[documents]
        I[models]
        J[vector-data]
    end
    
    D --> J
    E --> I
    B --> H
```

## Implementation Steps

### Step 1: Create Dockerfile for Main Application

Create `Dockerfile`:

```dockerfile
# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv pip install --system --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash rag_user

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY README.md ./

# Change ownership to non-root user
RUN chown -R rag_user:rag_user /app

# Switch to non-root user
USER rag_user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.rag_system.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Reverse proxy and load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - frontend
    networks:
      - rag_network
    restart: unless-stopped

  # Main API service
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - VECTORDB_URL=http://vectordb:8000
      - OLLAMA_URL=http://ollama:11434
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://rag_user:rag_pass@postgres:5432/rag_db
    volumes:
      - documents:/app/data/documents
      - logs:/app/logs
    depends_on:
      - vectordb
      - ollama
      - redis
      - postgres
    networks:
      - rag_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  # Frontend service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    networks:
      - rag_network
    restart: unless-stopped

  # Vector database
  vectordb:
    image: chromadb/chroma:latest
    environment:
      - CHROMA_SERVER_AUTH_CREDENTIALS_PROVIDER=chromadb.auth.providers.HtpasswdConfigServerAuthCredentialsProvider
      - CHROMA_SERVER_AUTH_CREDENTIALS_FILE=/chroma/auth/htpasswd
    volumes:
      - vector_data:/chroma/chroma
      - ./config/chroma/htpasswd:/chroma/auth/htpasswd:ro
    ports:
      - "8001:8000"  # Expose for development only
    networks:
      - rag_network
    restart: unless-stopped

  # Local LLM inference
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_ORIGINS=http://api:8000
    networks:
      - rag_network
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Redis for caching and sessions
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass rag_redis_pass
    volumes:
      - redis_data:/data
    networks:
      - rag_network
    restart: unless-stopped

  # PostgreSQL for user management and metadata
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=rag_db
      - POSTGRES_USER=rag_user
      - POSTGRES_PASSWORD=rag_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - rag_network
    restart: unless-stopped

volumes:
  documents:
    driver: local
  vector_data:
    driver: local
  ollama_models:
    driver: local
  redis_data:
    driver: local
  postgres_data:
    driver: local
  logs:
    driver: local

networks:
  rag_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Step 3: Create Development Override

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      target: builder
    volumes:
      - .:/app
      - /app/.venv
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - RELOAD=true
    command: ["uvicorn", "src.rag_system.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
  frontend:
    volumes:
      - ./frontend:/app
    command: ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]

  nginx:
    ports:
      - "8080:80"  # Different port for development
```

### Step 4: Create Configuration Files

Create `config/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        server api:8000;
    }
    
    upstream frontend_backend {
        server frontend:8501;
    }

    server {
        listen 80;
        server_name localhost;

        # API routes
        location /api/ {
            proxy_pass http://api_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Frontend routes
        location / {
            proxy_pass http://frontend_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Streamlit
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### Step 5: Create Management Scripts

Create `scripts/docker-management.sh`:

```bash
#!/bin/bash

# Docker management script for RAG system

set -e

COMPOSE_FILE="docker-compose.yml"
DEV_COMPOSE_FILE="docker-compose.dev.yml"

case "$1" in
    "dev")
        echo "Starting development environment..."
        docker-compose -f $COMPOSE_FILE -f $DEV_COMPOSE_FILE up --build
        ;;
    "prod")
        echo "Starting production environment..."
        docker-compose -f $COMPOSE_FILE up -d --build
        ;;
    "stop")
        echo "Stopping all services..."
        docker-compose down
        ;;
    "logs")
        service="${2:-}"
        if [ -n "$service" ]; then
            docker-compose logs -f "$service"
        else
            docker-compose logs -f
        fi
        ;;
    "shell")
        service="${2:-api}"
        docker-compose exec "$service" /bin/bash
        ;;
    "clean")
        echo "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|logs|shell|clean}"
        echo "  dev    - Start development environment"
        echo "  prod   - Start production environment"
        echo "  stop   - Stop all services"
        echo "  logs   - Show logs (optionally for specific service)"
        echo "  shell  - Open shell in service (default: api)"
        echo "  clean  - Clean up all Docker resources"
        exit 1
        ;;
esac
```

## Development Workflow

### Local Development

```bash
# Start development environment
./scripts/docker-management.sh dev

# View logs
./scripts/docker-management.sh logs api

# Access shell in container
./scripts/docker-management.sh shell api

# Stop development environment
./scripts/docker-management.sh stop
```

### Production Deployment

```bash
# Start production environment
./scripts/docker-management.sh prod

# Check service health
docker-compose ps

# View production logs
./scripts/docker-management.sh logs
```

## Security Considerations

### Container Security
- Non-root user in containers
- Read-only filesystems where possible
- Resource limits to prevent DoS
- Network isolation between services

### Secrets Management
- Use Docker secrets for production
- Environment variables for development
- Separate credentials per environment

### Network Security
- Internal network for service communication
- Reverse proxy for external access
- No direct exposure of internal services

## Definition of Done

### Infrastructure
- [ ] Dockerfile builds successfully
- [ ] Docker Compose starts all services
- [ ] Services can communicate internally
- [ ] Health checks are working
- [ ] Volume persistence verified

### Development Experience
- [ ] Hot reload working in development mode
- [ ] Logs accessible and meaningful
- [ ] Easy container shell access
- [ ] Development/production parity maintained

### Production Readiness
- [ ] Non-root containers
- [ ] Resource limits configured
- [ ] Security best practices implemented
- [ ] Backup strategy for volumes defined

### Documentation
- [ ] Docker setup instructions clear
- [ ] Management scripts documented
- [ ] Troubleshooting guide created

## Common Issues and Solutions

### Issue 1: Port Conflicts
**Solution**: Check for conflicting services on host ports
```bash
netstat -tulpn | grep :8000
```

### Issue 2: Permission Errors
**Solution**: Ensure proper ownership of volumes
```bash
sudo chown -R 1000:1000 ./data
```

### Issue 3: Out of Memory Errors
**Solution**: Increase Docker memory limits or add swap

## Next Steps

1. Proceed to [Task 1.3: RAG Pipeline Implementation](task-1-3-rag-pipeline.md)
2. Test deployment on target production environment
3. Set up monitoring and alerting for containers

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Container Security Best Practices](https://www.docker.com/blog/intro-guide-to-dockerfile-best-practices/) 