# Test Plan: Development Environment Setup Validation

**ID**: TEST-PLAN-001  
**Work Items**: [STORY-001](../stories/STORY-001.md), [TASK-001](../tasks/TASK-001.md), [TASK-002](../tasks/TASK-002.md), [TASK-003](../tasks/TASK-003.md)  
**Test Type**: Integration  
**Team**: Platform Engineering  
**Status**: Ready  
**Priority**: P1  
**Created**: 2025-06-12  
**Updated**: 2025-06-12  
**Test Lead**: QA Engineer  
**Reviewers**: Backend Engineer, DevOps Engineer

## Introduction

### Test Goal

Validate that the development environment setup process works consistently across different machines and operating systems, ensuring new developers can successfully configure and run the complete RAG pipeline within 30 minutes.

### Scope

**Included:**

- Fresh Python environment setup with uv package manager
- Dependency installation and version locking
- Code quality tools configuration (ruff, pytest)
- Basic RAG pipeline execution
- Docker Compose service startup

**Excluded:**

- Production deployment configurations
- Advanced Docker optimization
- Cross-platform performance benchmarking

### Work Items Under Test

- [STORY-001](../stories/STORY-001.md): Development Environment Setup
- [TASK-001](../tasks/TASK-001.md): Python project configuration with uv
- [TASK-002](../tasks/TASK-002.md): Docker Compose setup
- [TASK-003](../tasks/TASK-003.md): Code quality tools setup

### Success Criteria

- All test cases pass on Windows, macOS, and Linux
- Setup time consistently under 30 minutes for new developers
- All dependencies install without conflicts
- Code quality tools run without errors
- Docker services start successfully

## Test Environment Setup

### Prerequisites

- Fresh operating system (Windows 10+, macOS 12+, Ubuntu 20.04+)
- Python 3.11+ installed
- Docker and Docker Compose installed
- Git client configured
- Internet connection for package downloads

### Environment Creation

1. **Fresh Git Clone**: Always start with clean repository clone

   ```bash
   git clone <repository-url>
   cd on_prem_rag
   ```

2. **Clean Python Environment**: Remove any existing virtual environments

   ```bash
   # Remove any existing .venv directories
   rm -rf .venv
   ```

3. **Timer Setup**: Record start time for setup duration validation

### Data Preparation

- Test documents: Prepare sample PDF, DOCX, and TXT files
- Size: Files should be 1-5 pages to ensure quick processing
- Content: Include text that can be used for Q&A validation

### Cleanup Instructions

- Delete virtual environments between test runs
- Remove Docker volumes: `docker compose down -v`
- Clear Python cache: `find . -type d -name __pycache__ -delete`

## Test Cases

### TC-001: Python Environment and uv Setup

**Work Item**: [TASK-001](../tasks/TASK-001.md)  
**Objective**: Verify uv package manager setup and dependency installation  
**Preconditions**: Fresh repository clone, Python 3.11+ available

**Execution Steps**:

1. Install uv package manager following README instructions
2. Run `uv --version` to verify installation
3. Execute `uv install` to create virtual environment and install dependencies
4. Verify `uv.lock` file exists and contains pinned versions
5. Activate virtual environment: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
6. Run `uv run python --version` to confirm Python version

**Acceptance Criteria**:

- [ ] uv installs successfully without errors
- [ ] Virtual environment creates in under 2 minutes
- [ ] All dependencies install with locked versions
- [ ] Python version matches project requirements (3.11+)
- [ ] No dependency conflicts reported

**Cleanup**: Deactivate virtual environment

### TC-002: Code Quality Tools Configuration

**Work Item**: [TASK-003](../tasks/TASK-003.md)  
**Objective**: Validate ruff linting and pytest configuration  
**Preconditions**: Python environment from TC-001 activated

**Execution Steps**:

1. Run `uv run ruff check .` to verify linting configuration
2. Run `uv run ruff format --check .` to verify formatting rules
3. Execute `uv run pytest --version` to confirm pytest installation
4. Run `uv run pytest tests/` to execute test suite
5. Verify pre-commit hooks install: `uv run pre-commit install`
6. Test pre-commit: `uv run pre-commit run --all-files`

**Acceptance Criteria**:

- [ ] Ruff runs without configuration errors
- [ ] Code formatting rules apply consistently
- [ ] Pytest discovers and runs all tests
- [ ] Test coverage report generates successfully
- [ ] Pre-commit hooks install and execute

**Cleanup**: None required

### TC-003: Docker Compose Service Startup

**Work Item**: [TASK-002](../tasks/TASK-002.md)  
**Objective**: Verify all Docker services start and communicate properly  
**Preconditions**: Docker and Docker Compose installed

**Execution Steps**:

1. Review `docker-compose.yml` for service definitions
2. Run `docker compose up -d` to start services in detached mode
3. Verify services start: `docker compose ps`
4. Check logs for errors: `docker compose logs`
5. Test service connectivity:
   - ChromaDB: Verify port 8000 responds
   - Ollama: Verify port 11434 responds
   - Application: Verify configured port responds
6. Run health checks for each service

**Acceptance Criteria**:

- [ ] All defined services start without errors
- [ ] Service ports are accessible and respond
- [ ] No critical errors in service logs
- [ ] Services can communicate with each other
- [ ] Health checks pass for all services

**Cleanup**: Run `docker compose down -v` to stop and remove volumes

### TC-004: End-to-End RAG Pipeline Test

**Work Item**: [STORY-001](../stories/STORY-001.md)  
**Objective**: Validate complete RAG pipeline functionality  
**Preconditions**: All previous test cases passed, services running

**Execution Steps**:

1. Upload test document through configured interface
2. Verify document processing completes successfully
3. Check vector embeddings are created and stored
4. Submit test question related to uploaded document
5. Verify answer generation with source citations
6. Confirm response time meets performance requirements
7. Test error handling with invalid inputs

**Acceptance Criteria**:

- [ ] Document upload and processing completes under 5 minutes
- [ ] Vector embeddings are successfully stored
- [ ] Q&A generates relevant answers with citations
- [ ] Response time under 30 seconds for simple queries
- [ ] Error handling provides meaningful feedback

**Cleanup**: Clear test documents from vector store

### TC-005: Setup Time Validation

**Work Item**: [STORY-001](../stories/STORY-001.md)  
**Objective**: Confirm setup completes within 30-minute requirement  
**Preconditions**: Fresh environment, timer started

**Execution Steps**:

1. Follow complete setup guide from README
2. Record time for each major step:
   - Repository clone: < 2 minutes
   - uv installation: < 5 minutes
   - Dependency installation: < 10 minutes
   - Docker service startup: < 10 minutes
   - Pipeline verification: < 5 minutes
3. Document any blocking issues or delays
4. Stop timer when RAG pipeline is functional

**Acceptance Criteria**:

- [ ] Total setup time under 30 minutes
- [ ] No manual intervention required beyond documented steps
- [ ] All services functional at completion
- [ ] Documentation accurately reflects actual process
- [ ] New developer can follow instructions independently

**Cleanup**: Environment remains for additional testing

## Cross-Platform Validation

### TC-006: Windows Environment Test

**Work Item**: [STORY-001](../stories/STORY-001.md)  
**Objective**: Validate setup on Windows 10+ systems  
**Preconditions**: Windows 10+ with PowerShell/Command Prompt

**Execution Steps**:

1. Execute all previous test cases on Windows environment
2. Verify Windows-specific path handling
3. Test PowerShell and Command Prompt compatibility
4. Validate Docker Desktop integration
5. Check file permission handling

**Acceptance Criteria**:

- [ ] All test cases pass on Windows
- [ ] Path separators handle correctly
- [ ] Docker Desktop integrates properly
- [ ] File permissions work as expected
- [ ] Performance meets requirements

### TC-007: macOS Environment Test

**Work Item**: [STORY-001](../stories/STORY-001.md)  
**Objective**: Validate setup on macOS 12+ systems  
**Preconditions**: macOS 12+ with Terminal access

**Execution Steps**:

1. Execute all previous test cases on macOS environment
2. Test Homebrew package manager integration
3. Verify Xcode command line tools compatibility
4. Test Docker Desktop for Mac integration
5. Validate file system case sensitivity handling

**Acceptance Criteria**:

- [ ] All test cases pass on macOS
- [ ] Homebrew integration works properly
- [ ] Docker Desktop for Mac functions correctly
- [ ] Case sensitivity handled appropriately
- [ ] Performance meets requirements

### TC-008: Linux Environment Test

**Work Item**: [STORY-001](../stories/STORY-001.md)  
**Objective**: Validate setup on Ubuntu 20.04+ systems  
**Preconditions**: Ubuntu 20.04+ with bash shell

**Execution Steps**:

1. Execute all previous test cases on Linux environment
2. Test apt package manager integration
3. Verify systemd service management
4. Test Docker Engine (non-Desktop) integration
5. Validate file permissions and ownership

**Acceptance Criteria**:

- [ ] All test cases pass on Linux
- [ ] Package manager integration works
- [ ] Docker Engine functions correctly
- [ ] File permissions set appropriately
- [ ] Performance meets requirements

## Post-Test Analysis

### Documentation Updates

- Update README with any discovered setup issues
- Document platform-specific considerations
- Add troubleshooting section for common problems
- Update time estimates based on test results

### Issue Tracking

- Log any bugs or improvements discovered during testing
- Create tasks for documentation updates
- Report performance issues if setup exceeds time limits
- Track cross-platform compatibility problems

---

**Test Execution Notes**: This test plan must be executed by human testers who can verify the setup process from a new developer perspective. AI agents cannot check off the acceptance criteria - only humans can confirm the environment works correctly.
