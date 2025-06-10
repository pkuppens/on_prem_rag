# Project Structure

## Overview

This document describes the recommended project structure for better organization and maintainability.

## Directory Structure

```
.
├── src/                    # Source code root
│   ├── backend/           # Backend application code
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core business logic
│   │   ├── models/       # Data models
│   │   └── services/     # Business services
│   └── frontend/         # Frontend application code
│       ├── src/          # Frontend source
│       ├── public/       # Static assets
│       └── package.json  # Frontend dependencies
├── tests/                 # Test files
│   ├── backend/          # Backend tests
│   ├── frontend/         # Frontend tests
│   └── test_data/        # Test data
├── docs/                  # Documentation (technical)
├── project/               # Documentation (project management)
├── scripts/              # Utility scripts
├── uploaded_files/       # User uploaded files
├── docker/               # Docker-related files
│   ├── backend/         # Backend Dockerfile
│   └── frontend/        # Frontend Dockerfile
├── pyproject.toml        # Python project configuration
└── docker-compose.yml    # Docker Compose configuration
```

## Benefits

1. **Clear Separation**: Backend and frontend code are clearly separated
2. **Better Organization**: Related files are grouped together
3. **Easier Testing**: Test files mirror the source structure
4. **Simplified Docker**: Each component has its own Dockerfile
5. **Improved Maintainability**: Clear boundaries between components

## Migration Steps

1. Create the new directory structure
2. Move existing files to their new locations
3. Update import paths and references
4. Update Docker configurations
5. Update documentation

## Docker Considerations

- Each component (backend, frontend) has its own Dockerfile
- Shared configuration in docker-compose.yml
- Volume mounts for development
- Proper networking between services

## Development Workflow

1. Backend development in `src/backend`
2. Frontend development in `src/frontend`
3. Tests in corresponding `tests/` directories
4. Documentation in `docs/`
5. Docker configurations in `docker/`
