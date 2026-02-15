# Test Agent: Detect and Execute Tests with Service Management

## Purpose

This command detects and executes all tests in the project, including integration tests that require services to be started. It automatically manages service lifecycle (Docker services, MCP servers) and uses parallelism where possible to optimize test execution time.

## When to Use

- Before committing code to ensure all tests pass
- After making changes to verify functionality
- During development to run specific test suites
- In CI/CD pipelines for automated testing
- When debugging test failures
- To validate integration between services

## Prerequisites

Before running this command, ensure:

- [ ] Python environment is set up with required dependencies (`uv sync`)
- [ ] Docker and Docker Compose are installed (for integration tests)
- [ ] Git is installed and accessible
- [ ] You have write access to test output directories
- [ ] Network connectivity (for internet-required tests)

## Command Execution Workflow

### Step 1: Verify Prerequisites

#### 1.1 Check Python Environment

**Cross-platform:**

```bash
python --version
```

**Expected**: Python 3.12 or higher

#### 1.2 Check Dependencies

**Cross-platform:**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Check if uv is available
uv --version

# Sync dependencies
uv sync --dev
```

#### 1.3 Check Docker (for integration tests)

**Cross-platform:**

```bash
docker --version
docker compose version
```

**Expected**: Docker and Docker Compose v2 installed

### Step 2: Run Test Agent

#### 2.1 Basic Test Execution

**Cross-platform:**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Run all tests with automatic service management
# The script will automatically use 'uv run pytest' if uv is available
python scripts/run_tests.py
```

**Note:** The script automatically detects if `uv` is available and uses `uv run pytest` internally. You don't need to use `uv run` to execute the script itself - just run it with `python`.

**What it does:**

- Detects all tests in the `tests/` directory
- Identifies integration tests that require services
- Starts required Docker services (ChromaDB, Ollama, backend, auth)
- Starts MCP Calendar Server if needed
- Runs tests in parallel where possible
- Handles test failures and attempts fixes
- Cleans up services after test completion

#### 2.2 Test Execution Options

**Run specific test file:**

```bash
python scripts/run_tests.py --file tests/test_chunking.py
```

**Run tests matching pattern:**

```bash
python scripts/run_tests.py --pattern "test_embedding"
```

**Run only unit tests (skip integration):**

```bash
python scripts/run_tests.py --unit-only
```

**Run only integration tests:**

```bash
python scripts/run_tests.py --integration-only
```

**Run with specific markers:**

```bash
python scripts/run_tests.py --markers "slow and not internet"
```

**Run with verbose output:**

```bash
python scripts/run_tests.py --verbose
```

**Run without parallel execution:**

```bash
python scripts/run_tests.py --no-parallel
```

**Keep services running after tests:**

```bash
python scripts/run_tests.py --keep-services
```

**Fix issues automatically:**

```bash
python scripts/run_tests.py --auto-fix
```

### Step 3: Review Test Results

#### 3.1 Test Output

The test agent provides:

- **Test Discovery**: List of all discovered tests
- **Service Status**: Status of required services
- **Test Execution**: Progress and results for each test
- **Summary Report**: Overall test results with pass/fail counts
- **Failure Details**: Detailed error messages for failed tests
- **Fix Attempts**: Log of automatic fixes attempted

#### 3.2 Expected Output

```
🔍 Test Agent: Detecting and executing tests...

📋 Test Discovery:
   - Found 57 test files
   - 42 unit tests
   - 15 integration tests

🔧 Service Management:
   ✅ ChromaDB: Running (port 9182)
   ✅ Ollama: Running (port 11434)
   ⚠️  MCP Calendar Server: Not running (will start if needed)
   ✅ Backend: Running (port 9180)
   ✅ Auth: Running (port 9181)

🚀 Test Execution:
   Running tests in parallel (4 workers)...
   
   tests/test_chunking.py::test_chunk_boundaries ................. PASSED
   tests/test_embeddings.py::test_embedding_shape ................ PASSED
   tests/test_mcp_calendar_server.py::TestMCPCalendarServer ..... SKIPPED (no MCP server)
   ...

📊 Test Summary:
   ✅ Passed: 48
   ❌ Failed: 2
   ⏭️  Skipped: 7
   ⏱️  Duration: 2m 34s

🔧 Auto-Fix Attempts:
   ✅ Fixed: test_imports.py - Added missing import
   ❌ Could not fix: test_embedding_shapes.py - Manual intervention required
```

### Step 4: Handle Test Failures

#### 4.1 Automatic Fixes

The test agent attempts to automatically fix common issues:

- **Missing imports**: Adds required imports
- **Syntax errors**: Fixes common syntax issues
- **Configuration issues**: Updates test configuration
- **Service connection issues**: Restarts services and retries

#### 4.2 Manual Intervention

For issues that cannot be automatically fixed:

1. Review the failure details in the test output
2. Check service logs if integration tests failed
3. Review the test code and fix manually
4. Re-run the specific test to verify the fix

#### 4.3 Service Troubleshooting

**Check Docker services:**

```bash
docker compose ps
docker compose logs
```

**Check MCP Calendar Server:**

```bash
# Check if server is running
ps aux | grep mcp-calendar-server

# Start server manually if needed
uv run mcp-calendar-server
```

**Restart services:**

```bash
docker compose restart
```

## Integration Test Requirements

### Docker Services

The following Docker services may be required for integration tests:

- **ChromaDB**: Vector database (port 9182)
- **Ollama**: LLM service (port 11434)
- **Backend**: RAG pipeline API (port 9180)
- **Auth**: Authentication service (port 9181)
- **Frontend**: Frontend application (port 5173)

### MCP Calendar Server

Some tests require the MCP Calendar Server to be running:

- Server must be started before running calendar integration tests
- Server runs on a configurable port (default: varies)
- Requires Google Calendar API credentials

### Service Startup Order

The test agent starts services in the correct order:

1. ChromaDB (vector database)
2. Ollama (LLM service)
3. Backend (depends on ChromaDB and Ollama)
4. Auth (authentication service)
5. MCP Calendar Server (if needed)

## Parallel Execution

The test agent uses `pytest-xdist` for parallel test execution:

- **Default**: Uses `auto` mode (detects CPU count)
- **Manual**: Specify worker count with `--workers N`
- **Disabled**: Use `--no-parallel` for sequential execution

**Note**: Integration tests that share resources may need sequential execution to avoid conflicts.

## Test Markers

The test agent respects pytest markers:

- `slow`: Slow-running tests (may be skipped in fast runs)
- `internet`: Tests requiring internet connectivity
- `fts5`: Tests requiring SQLite FTS5 extension
- `ci_setup`: CI/CD setup validation tests

**Filter by markers:**

```bash
uv run python scripts/run_tests.py --markers "not slow and not internet"
```

## Cleanup

### Automatic Cleanup

The test agent automatically:

- Stops Docker services after tests (unless `--keep-services`)
- Cleans up test artifacts
- Removes temporary test data
- Closes MCP server connections

### Manual Cleanup

**Stop all services:**

```bash
docker compose down
```

**Clean up test artifacts:**

```bash
rm -rf tests/test_temp/*
```

**Reset test data:**

```bash
# Remove test database files
rm -f data/test_*.db
```

## Troubleshooting

### Common Issues

#### Issue: Tests fail with "Service not available"

**Solution:**

1. Check if Docker services are running: `docker compose ps`
2. Start services manually: `docker compose up -d`
3. Wait for services to be ready (check logs)
4. Re-run tests

#### Issue: MCP Calendar Server tests are skipped

**Solution:**

1. Start MCP Calendar Server: `uv run mcp-calendar-server`
2. Verify server is running: Check process list
3. Re-run tests

#### Issue: Parallel execution causes conflicts

**Solution:**

1. Run tests sequentially: `--no-parallel`
2. Or reduce worker count: `--workers 2`

#### Issue: Tests timeout

**Solution:**

1. Increase timeout: `--timeout 300`
2. Check service health: `docker compose ps`
3. Review test logs for slow operations

### Debug Mode

Enable verbose output for debugging:

```bash
uv run python scripts/run_tests.py --verbose --debug
```

This provides:

- Detailed service startup logs
- Test execution details
- Service health checks
- Connection attempts

## Best Practices

1. **Run tests frequently**: Catch issues early
2. **Use specific test filters**: Run only relevant tests during development
3. **Keep services running**: Use `--keep-services` during active development
4. **Review failures**: Don't ignore test failures, fix them promptly
5. **Use markers**: Mark tests appropriately for better organization
6. **Parallel execution**: Use parallel execution for faster feedback (when safe)

## Related Commands

- `uv run pytest` - Direct pytest execution (manual service management)
- `docker compose up` - Manual Docker service startup
- `uv run mcp-calendar-server` - Manual MCP Calendar Server startup

## Code Files

- [scripts/run_tests.py](scripts/run_tests.py) - Main test agent implementation
- [tests/conftest.py](tests/conftest.py) - Test configuration and fixtures
- [pyproject.toml](pyproject.toml) - Pytest configuration and dependencies
- [docker-compose.yml](docker-compose.yml) - Docker service definitions
