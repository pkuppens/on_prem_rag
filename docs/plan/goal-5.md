# Goal 5: Deployment & Infrastructure

## Context from Business Objective

This goal enables production deployment with enterprise standards, establishing robust infrastructure that supports scalability, monitoring, and maintenance. The deployment must be reliable, secure, and maintainable for enterprise environments.

## Objective

Build a comprehensive deployment and infrastructure system using Docker containerization, modern development tooling, performance monitoring, and CI/CD pipelines. This ensures the RAG solution can be deployed consistently across different environments.

## Core Features

- Docker containerization with multi-service architecture
- Development tooling (uv, ruff, pytest) for code quality
- Performance monitoring and alerting
- CI/CD pipeline for automated deployments
- Backup and disaster recovery procedures
- Resource optimization and scaling strategies

## Business Impact

**Enable production deployment with enterprise standards**

### Operational Excellence
- **Consistent Deployments**: Identical environments across dev/staging/production
- **Automated Quality**: CI/CD prevents deployment of broken code
- **Proactive Monitoring**: Early detection of performance issues
- **Disaster Recovery**: Business continuity in case of failures

### Cost Efficiency
- **Resource Optimization**: Right-sizing infrastructure for workloads
- **Automated Operations**: Reduced manual intervention and errors
- **Scaling on Demand**: Pay only for resources actually needed
- **Maintenance Automation**: Reduce operational overhead

## Technical Implementation

### Docker Compose Configuration

**Production Architecture**:

```yaml
version: '3.8'
services:
  rag-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama
      - postgres

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ragdb
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  ollama_data:
  postgres_data:
```

### Infrastructure Architecture

```mermaid
graph TB
    A[Load Balancer] --> B[RAG Backend]
    A --> C[RAG Backend Replica]
    
    B --> D[Ollama Service]
    C --> D
    
    B --> E[PostgreSQL Primary]
    C --> F[PostgreSQL Replica]
    
    B --> G[ChromaDB]
    C --> G
    
    H[Monitoring Stack] --> B
    H --> C
    H --> D
    H --> E
    
    I[Backup System] --> E
    I --> G
```

## Container Architecture

### Application Container (RAG Backend)

**Dockerfile**:

```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy requirements and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Service Configuration

```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "On-Premises RAG"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str
    
    # Security
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    
    # LLM Configuration
    ollama_endpoint: str = "http://ollama:11434"
    default_model: str = "mistral:7b"
    
    # Vector Database
    chroma_persist_directory: str = "/app/data/vectordb"
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Development Tooling

### Modern Python Toolchain

**pyproject.toml**:

```toml
[project]
name = "on-prem-rag"
version = "0.1.0"
description = "On-premises RAG solution for enterprise document analysis"
requires-python = ">=3.11"

dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "langchain>=0.1.0",
    "chromadb>=0.4.0",
    "ollama>=0.1.7",
    "psycopg2-binary>=2.9.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "pydantic>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.6",
    "black>=23.9.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.0",
    "pre-commit>=3.5.0",
]

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "N",  # pep8-naming
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Code Quality Automation

**.pre-commit-config.yaml**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Performance Monitoring

### Application Metrics

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
from functools import wraps

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users', 'Number of active users')
LLM_RESPONSE_TIME = Histogram('llm_response_time_seconds', 'LLM response time')
VECTOR_SEARCH_TIME = Histogram('vector_search_time_seconds', 'Vector search time')

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)
    return wrapper

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

```python
# src/health/checks.py
from fastapi import HTTPException
import asyncio

class HealthChecker:
    """Comprehensive health checking system."""
    
    async def check_database(self) -> dict:
        """Check database connectivity."""
        try:
            # Simple database query
            result = await self.db.execute("SELECT 1")
            return {"status": "healthy", "response_time": "< 100ms"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_ollama(self) -> dict:
        """Check Ollama service availability."""
        try:
            response = await self.ollama_client.list_models()
            return {"status": "healthy", "models": len(response.models)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_vector_db(self) -> dict:
        """Check ChromaDB availability."""
        try:
            collection_count = len(self.chroma_client.list_collections())
            return {"status": "healthy", "collections": collection_count}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    health_checker = HealthChecker()
    
    checks = await asyncio.gather(
        health_checker.check_database(),
        health_checker.check_ollama(),
        health_checker.check_vector_db(),
        return_exceptions=True
    )
    
    overall_status = "healthy" if all(
        check.get("status") == "healthy" for check in checks
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": checks[0],
            "ollama": checks[1],
            "vector_db": checks[2]
        }
    }
```

## CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/ci.yml**:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_ragdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install uv
      uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    
    - name: Set up Python
      run: uv python install 3.11
    
    - name: Install dependencies
      run: uv sync --all-extras
    
    - name: Run linting
      run: uv run ruff check .
    
    - name: Run formatting check
      run: uv run ruff format --check .
    
    - name: Run type checking
      run: uv run mypy src/
    
    - name: Run tests
      run: uv run pytest --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_ragdb
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Build Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: false
        tags: rag-system:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: [test, build]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add deployment commands here
```

## Backup and Disaster Recovery

### Automated Backup System

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec postgres pg_dump -U ${DB_USER} ${DB_NAME} | gzip > "${BACKUP_DIR}/postgres_${TIMESTAMP}.sql.gz"

# ChromaDB backup
echo "Backing up ChromaDB..."
tar -czf "${BACKUP_DIR}/chromadb_${TIMESTAMP}.tar.gz" ./data/vectordb/

# Application data backup
echo "Backing up application data..."
tar -czf "${BACKUP_DIR}/appdata_${TIMESTAMP}.tar.gz" ./data/

# Cleanup old backups (keep 30 days)
find ${BACKUP_DIR} -name "*.gz" -mtime +30 -delete

echo "Backup completed: ${TIMESTAMP}"
```

### Disaster Recovery Procedures

```bash
#!/bin/bash
# scripts/restore.sh

set -e

BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241215_143000"
    exit 1
fi

BACKUP_DIR="/backups"

# Stop services
echo "Stopping services..."
docker-compose down

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
gunzip -c "${BACKUP_DIR}/postgres_${BACKUP_DATE}.sql.gz" | docker exec -i postgres psql -U ${DB_USER} ${DB_NAME}

# Restore ChromaDB
echo "Restoring ChromaDB..."
rm -rf ./data/vectordb
tar -xzf "${BACKUP_DIR}/chromadb_${BACKUP_DATE}.tar.gz"

# Restore application data
echo "Restoring application data..."
tar -xzf "${BACKUP_DIR}/appdata_${BACKUP_DATE}.tar.gz"

# Start services
echo "Starting services..."
docker-compose up -d

echo "Restore completed from backup: ${BACKUP_DATE}"
```

## Resource Optimization

### Auto-scaling Configuration

```yaml
# docker-compose.override.yml (for production)
version: '3.8'
services:
  rag-backend:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first

  ollama:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 16G
        reservations:
          cpus: '2.0'
          memory: 8G
```

### Performance Tuning

```python
# src/config/performance.py
import asyncio
from contextlib import asynccontextmanager

class PerformanceOptimizer:
    """Optimizes application performance settings."""
    
    def __init__(self):
        self.connection_pool_size = 20
        self.max_concurrent_requests = 100
        self.request_timeout = 30
        
    def configure_uvicorn(self):
        """Configure Uvicorn for optimal performance."""
        return {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 1,  # Single worker for simplicity
            "loop": "uvloop",
            "http": "httptools",
            "limit_concurrency": self.max_concurrent_requests,
            "timeout_keep_alive": 5,
        }
    
    @asynccontextmanager
    async def request_semaphore(self):
        """Limit concurrent requests to prevent overload."""
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        async with semaphore:
            yield
```

## Implementation Tasks

### Task 5.1: Container Infrastructure
- Docker container optimization
- Multi-service orchestration
- Resource limits and monitoring
- Health checks and readiness probes

### Task 5.2: Development Pipeline
- CI/CD workflow setup
- Automated testing integration
- Code quality enforcement
- Deployment automation

### Task 5.3: Monitoring System
- Application metrics collection
- Performance monitoring
- Alerting configuration
- Log aggregation and analysis

### Task 5.4: Backup & Recovery
- Automated backup procedures
- Disaster recovery testing
- Data integrity verification
- Recovery time optimization

## Success Criteria

### Infrastructure Requirements
- [ ] Docker containers deployed and running stably
- [ ] CI/CD pipeline executing successfully
- [ ] Monitoring and alerting functional
- [ ] Backup and recovery procedures tested

### Performance Requirements
- [ ] Application starts within 60 seconds
- [ ] Handles 50+ concurrent users
- [ ] 99.9% uptime during business hours
- [ ] Recovery time objective (RTO) < 4 hours

### Operational Requirements
- [ ] Automated deployments working
- [ ] Monitoring alerts configured
- [ ] Backup procedures validated
- [ ] Documentation complete for operations

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Container Failures** | High | Health checks, automatic restarts, redundancy |
| **Data Loss** | Critical | Automated backups, replication, tested recovery |
| **Performance Degradation** | Medium | Monitoring, auto-scaling, resource limits |
| **Deployment Failures** | Medium | Blue-green deployment, rollback procedures |

## Timeline & Priority

**Timeline**: 2-3 weeks | **Priority**: Medium | **Dependencies**: Goals 1, 3

### Week 1: Foundation
- Docker containerization
- Basic CI/CD pipeline
- Health checks implementation

### Week 2: Enhancement
- Performance monitoring
- Backup system setup
- Auto-scaling configuration

### Week 3: Production Readiness
- Security hardening
- Disaster recovery testing
- Documentation completion

## Next Steps

Upon completion of Goal 5:
1. Proceed to [Goal 6: Security Framework](goal-6.md)
2. Begin production deployment planning
3. Establish operational procedures

## Related Documentation

- [Goal 1: Technical Foundation](goal-1.md)
- [Goal 6: Security Framework](goal-6.md)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/) 