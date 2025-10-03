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

The git hook system consists of several files:

- `.git/hooks/pre-push` - Shell script for Unix-like systems (Linux, macOS)
- `.git/hooks/pre-push.ps1` - PowerShell script for Windows
- `scripts/setup_git_hooks.py` - Cross-platform setup script

### Setup Process

1. **Automatic Setup**: Run the setup script once after cloning the repository:
   ```bash
   uv run python scripts/setup_git_hooks.py
   ```

2. **Manual Setup**: The setup script detects the operating system and installs the appropriate hook:
   - **Windows**: Creates a batch file wrapper that calls the PowerShell script
   - **Unix-like**: Copies and makes executable the shell script

### Hook Behavior

The pre-push hook performs the following actions:

1. **Environment Validation**:
   - Verifies we're in a git repository
   - Checks for `pyproject.toml` to ensure we're in the project root
   - Validates that `uv` is installed and available

2. **Dependency Installation**:
   - Runs `uv sync --dev` to ensure all dependencies are installed
   - Fails if dependency installation fails

3. **Unit Test Execution**:
   - Runs `uv run pytest -m "not internet and not slow"` to execute fast unit tests
   - Uses the same test configuration as GitHub Actions
   - Excludes slow and internet-dependent tests for faster feedback

4. **Push Blocking**:
   - Blocks the push if any tests fail
   - Provides clear error messages and instructions
   - Shows bypass options for emergency situations

## Emergency Bypass Mechanisms

In genuine emergency situations, the hook can be bypassed using two methods:

### Method 1: Environment Variable

```bash
# Unix-like systems
GIT_PUSH_BYPASS_TESTS=true git push

# Windows PowerShell
$env:GIT_PUSH_BYPASS_TESTS="true"; git push
```

### Method 2: Git No-Verify Flag

```bash
git push --no-verify
```

### Bypass Warnings

When bypassing the hook, you'll see warning messages:

```
[PRE-PUSH] BYPASS MODE: Skipping unit tests due to GIT_PUSH_BYPASS_TESTS=true
[PRE-PUSH] This should only be used in emergency situations!
```

## Configuration

### Test Selection

The hook runs tests with the marker `"not internet and not slow"`, which:

- **Includes**: Fast unit tests that don't require network access
- **Excludes**: Tests marked with `@pytest.mark.slow` or `@pytest.mark.internet`
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
2. **Use bypasses sparingly** and only in genuine emergencies
3. **Fix failing tests immediately** after using a bypass
4. **Keep the hook updated** when test configuration changes

### For Project Maintenance

1. **Update hook scripts** when test configuration changes
2. **Document any new bypass mechanisms** in this file
3. **Monitor hook effectiveness** through CI/CD success rates
4. **Review bypass usage** to identify potential process improvements

## Code Files

- [.git/hooks/pre-push](.git/hooks/pre-push) - Unix shell script for pre-push hook
- [.git/hooks/pre-push.ps1](.git/hooks/pre-push.ps1) - PowerShell script for Windows
- [scripts/setup_git_hooks.py](scripts/setup_git_hooks.py) - Cross-platform setup script
- [pyproject.toml](pyproject.toml) - Test configuration and dependencies
- [.github/workflows/python-ci.yml](.github/workflows/python-ci.yml) - CI/CD pipeline configuration

## References

- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [Pytest Markers Documentation](https://docs.pytest.org/en/stable/how-to/mark.html)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [Project Testing Standards](docs/technical/TEST_DOCUMENTATION.md)
