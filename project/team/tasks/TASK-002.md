# Task: Create Development Docker Compose Setup

**ID**: TASK-002
**Story**: [STORY-001: Development Environment Setup](../stories/STORY-001.md)
**Assignee**: DevOps Engineer
**Status**: Todo
**Effort**: 6 hours
**Created**: 2025-05-31
**Updated**: 2025-06-10

## Description

Set up a `docker-compose.yml` file in the project root that launches the FastAPI application and its dependencies for local development.
The current application state requires:

- FastAPI application (including test_app)
- SQLite-based vector store (ChromaDB SQLite version)
- No Ollama service needed at this stage

Ensure services can communicate on a shared network, files and databases are persisted, and support hot reloading of the apps.

## Acceptance Criteria

- [ ] Document the exact location of docker-compose.yml and the complete command to start services
- [ ] `docker-compose up` starts all services without errors (including test_app)
- [ ] Update configuration to use environment variables for settings like `allow_origins` instead of hardcoded values
- [ ] Application container mounts source code for live reload - including tests directory, test_data/, uploaded_files/
- [ ] Data volumes persist ChromaDB state between restarts
- [ ] Document the use of Docker volumes for data persistence
- [ ] Document how to share important folders (e.g. uploaded_files)
- [ ] Tests still pass locally
- [ ] Document how to run unit tests inside the container
- [ ] Create docs/TEST_DOCKER.md with instructions for testing the complete application inside Docker

## Dependencies

- **Blocked by**: [TASK-001 (project configuration)](TASK-001.md)
- **Blocks**: [TASK-015 (compose services for deployment)](TASK-015.md)

---

**Implementer**: DevOps Engineer
**Reviewer**: Lead Developer
**Target Completion**: TBD
