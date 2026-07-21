# Git Hooks for Unit Test Enforcement

This document describes the git hooks implemented to enforce unit test passing on every git push, ensuring code quality and preventing broken code from being pushed to remote repositories.

## Overview

The project implements a pre-push hook that automatically runs unit tests before allowing any git push operation. This ensures that:

- All pushes contain working code
- Unit tests pass before code reaches remote repositories
- Developers get immediate feedback on test failures
- CI/CD pipelines are less likely to fail due to test issues

## Implementation

### Hook Files

The git hook system consists of:

- `githooks/pre-push` - Tracked POSIX shell script; this is the single source of
  truth for the hook's behavior on both Windows and Unix. Git for Windows invokes
  hooks through its bundled `sh`, so the same script runs unmodified on both
  platforms — no OS branching or PowerShell wrapper needed.
- `scripts/setup_git_hooks.py` - Installs `githooks/pre-push` into
  `.git/hooks/pre-push` (the actual, untracked, git-managed hooks directory)

### Setup Process

1. **Automatic Setup**: Run the setup script once after cloning the repository:
   ```bash
   uv run python scripts/setup_git_hooks.py
   ```

2. The setup script copies the tracked `githooks/pre-push` template to
   `.git/hooks/pre-push` and marks it executable, then verifies the install by
   actually executing the hook with `PRE_PUSH_SELF_TEST=1` (which short-circuits
   to a no-op success) rather than only checking that the file exists — this
   catches interpreter-resolution failures instead of silently reporting a
   broken hook as configured.

### Hook Behavior

The pre-push hook performs the following actions:

1. **Environment Validation**:
   - Verifies we're in a git repository
   - Checks for `pyproject.toml` to ensure we're in the project root
   - Validates that `uv` is installed and available

2. **Dependency Installation**:
   - Runs `uv sync --group dev` to ensure all dependencies are installed
   - Fails if dependency installation fails

3. **Unit Test Execution**:
   - Runs `uv run pytest -m "not internet and not slow"` to execute fast unit tests
   - Uses the same test configuration as GitHub Actions
   - Excludes slow and internet-dependent tests for faster feedback

4. **Push Blocking**:
   - Blocks the push if any tests fail
   - Provides clear error messages and instructions
   - Shows bypass options for emergency situations

## Emergency Bypass Mechanism

In genuine emergency situations, the hook can be bypassed using the git no-verify flag:

```bash
git push --no-verify
```

### Bypass Warning

When bypassing the hook, you'll see a warning message:

```
[PRE-PUSH] BYPASS MODE: Skipping unit tests due to --no-verify flag
[PRE-PUSH] This should only be used in emergency situations!
```

## Configuration

### Test Selection

The hook runs tests with the marker `"not internet and not slow"`, which:

- **Includes**: Fast unit tests that don't require network access
- **Excludes**: Tests marked with `@pytest.mark.slow`, `@pytest.mark.internet`, or `@pytest.mark.ollama`
- **Rationale**: Provides fast feedback while excluding tests that might be flaky or slow

### Test Configuration

The hook uses the same pytest configuration as defined in `pyproject.toml`:

- Test discovery from `tests/` directory
- Python path includes `src` and `src/backend`
- Coverage reporting enabled
- Async test support via pytest-asyncio

## Troubleshooting

### Common Issues

1. **"uv is not installed"**:
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **"pyproject.toml not found"**:
   - Ensure you're running git commands from the project root directory

3. **"Not in a git repository"**:
   - Verify you're in a directory that contains a `.git` folder

4. **Hook not executable** (Unix-like systems):
   ```bash
   chmod +x .git/hooks/pre-push
   ```

### Debugging Test Failures

When tests fail, the hook provides guidance:

```bash
# Run tests with verbose output to see detailed failures
uv run pytest -v

# Run specific test file
uv run pytest tests/test_specific_file.py -v

# Run tests with coverage
uv run pytest --cov=src/backend --cov-report=term
```

## Integration with CI/CD

The pre-push hook complements the existing GitHub Actions CI/CD pipeline:

- **Pre-push hook**: Fast local validation with unit tests only
- **GitHub Actions**: Comprehensive testing including slow tests, integration tests, and security scans
- **Consistency**: Both use the same test configuration and markers

## Best Practices

### For Developers

1. **Run tests locally** before pushing to catch issues early
2. **Use bypass sparingly** and only in genuine emergencies
3. **Fix failing tests immediately** after using a bypass
4. **Keep the hook updated** when test configuration changes

### For Project Maintenance

1. **Update hook scripts** when test configuration changes
2. **Document any changes to bypass mechanisms** in this file
3. **Monitor hook effectiveness** through CI/CD success rates
4. **Review bypass usage** to identify potential process improvements

## Code Files

- [githooks/pre-push](../../githooks/pre-push) - Tracked POSIX hook script (source of truth)
- [scripts/setup_git_hooks.py](../../scripts/setup_git_hooks.py) - Setup script; installs the hook and verifies it executes
- [tests/test_setup_git_hooks.py](../../tests/test_setup_git_hooks.py) - Tests for the install/verify logic
- [pyproject.toml](../../pyproject.toml) - Test configuration and dependencies
- [.github/workflows/python-ci.yml](../../.github/workflows/python-ci.yml) - CI/CD pipeline configuration

## References

- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Pytest Markers Documentation](https://docs.pytest.org/en/stable/how-to/mark.html)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Project Testing Standards](docs/technical/TEST_DOCUMENTATION.md)
