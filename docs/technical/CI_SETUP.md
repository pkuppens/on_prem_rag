# CI/CD Setup Documentation

This document describes the CI/CD setup configuration, Python version constraints, and troubleshooting guide for the GitHub Actions workflow.

## Overview

The project uses GitHub Actions for continuous integration with a multi-job workflow that includes setup, linting, testing, and security scanning. The setup is designed to be reliable and efficient with proper caching and dependency management.

## Python Version Constraints

### Current Configuration

- **Python Version**: 3.12 (pinned)
- **Constraint**: `>=3.12,<3.14` in `pyproject.toml`
- **UV Configuration**: `python-version = "3.12"` in `[tool.uv]`

### Rationale

Python 3.12 is pinned to avoid compatibility issues with dependencies:

1. **pypika Incompatibility**: The `pypika==0.48.9` package (dependency of `chromadb>=0.4.0`) is incompatible with Python 3.14
2. **AST Changes**: Python 3.14 removed the `ast.Str` attribute, breaking pypika's build process
3. **Build Failures**: This causes `uv sync --dev` to fail with `AttributeError: module 'ast' has no attribute 'Str'`

### Version Management

The Python version is managed in multiple places:

- `pyproject.toml`: `requires-python = ">=3.12,<3.14"`
- `pyproject.toml`: `[tool.uv] python-version = "3.12"`
- `.github/workflows/python-ci.yml`: `python-version: ["3.12"]`

## GitHub Actions Workflow

### Job Structure

1. **Setup Job**: Installs dependencies and pre-downloads models
2. **Lint Job**: Runs code quality checks (depends on setup)
3. **Model Download Job**: Downloads embedding models (depends on setup)
4. **Unit Tests**: Fast tests that always run (depends on setup + model-download)
5. **Performance Tests**: Slow tests, conditional execution
6. **Integration Tests**: Internet-dependent tests, conditional execution
7. **Security Scan**: Vulnerability scanning (depends on setup)
8. **CI Summary**: Aggregates results from all jobs

### Cloud LLM Test (Manual)

The **Cloud LLM Test** workflow (`.github/workflows/cloud-llm.yml`) runs separately and is triggered manually only. Use it when Cloud LLM code (e.g. Gemini, llm_config) is changed. If `GEMINI_API_KEY` is not set, the test skips gracefully. Trigger via Actions → Cloud LLM Test → Run workflow.

### Environment Variables

Required environment variables for HuggingFace model caching:

```yaml
env:
  HF_HOME: ${{ github.workspace }}/.cache/huggingface
  TRANSFORMERS_CACHE: ${{ github.workspace }}/.cache/huggingface/hub
  SENTENCE_TRANSFORMERS_HOME: ${{ github.workspace }}/.cache/huggingface/sentence_transformers
```

### Caching Strategy

The workflow uses multiple cache layers:

1. **Python and uv** (via `astral-sh/setup-uv`): Python installs and UV dependency cache. Invalidates when `uv.lock` or `pyproject.toml` changes. First runs are slower; cached runs skip Python/UV install.
2. **HuggingFace Models**: Cached based on `scripts/setup_embedding_models.py` hash only—application code changes do not invalidate. Restore-keys allow reuse when the setup script is refactored but models are unchanged.
3. **Pytest Cache**: Cached based on test files and pyproject.toml. Speeds up test collection on subsequent runs.

## Local Validation

### Running CI Setup Tests

Before pushing changes, validate the setup locally:

```bash
# Run CI setup validation tests
uv run pytest tests/ci/test_github_actions_setup.py -v -m ci_setup

# Run all tests to ensure nothing is broken
uv run pytest -m "not internet and not slow"
```

### Manual Setup Validation

Test the setup process manually:

```bash
# Check Python version
python --version  # Should be 3.12.x

# Test uv sync
uv sync --dev

# Test embedding model setup
uv run python scripts/setup_embedding_models.py
```

## Disk Space (Private Repositories)

Private repository runners have ~14GB free disk. The workflow uses `jlumbroso/free-disk-space` to remove pre-installed tools (Android, .NET, Haskell, etc.), freeing ~30GB before `uv sync` and HuggingFace model downloads. Without this, "No space left on device" errors can occur.

Each job gets a fresh VM; runners are not shared between jobs. The free-disk-space step adds setup time (~2–5 min) but is required for all test jobs (unit, integration, performance) because they restore the HuggingFace cache and run coverage.

## Job Timeouts

| Job               | Timeout | Rationale                                                    |
|-------------------|---------|--------------------------------------------------------------|
| test-unit         | 30 min  | Temporary; reduce once runs stabilize. Includes setup + pytest. |
| test-performance  | 10 min  | Slow tests; sequential execution.                            |
| test-integration  | 15 min  | Internet-dependent; sequential execution.                    |

## Troubleshooting

### Common Issues

#### 1. Python 3.14 Build Failures

**Symptoms**: `AttributeError: module 'ast' has no attribute 'Str'` during `uv sync`

**Cause**: pypika package incompatibility with Python 3.14

**Solution**: Ensure Python 3.12 is being used:
```bash
# Check current Python version
python --version

# Force Python 3.12 with uv
uv python install 3.12
uv sync --python 3.12 --dev
```

#### 2. UV Installation Failures

**Symptoms**: `astral-sh/setup-uv` fails or times out

**Cause**: Network issues or GitHub Actions runner problems

**Solution**: 
- Check network connectivity
- Verify the setup-uv action version (v7) is available
- Consider using a different runner or retry mechanism

#### 3. Dependency Resolution Failures

**Symptoms**: `uv sync` fails with dependency conflicts

**Cause**: Incompatible dependency versions

**Solution**:
- Check `pyproject.toml` for version constraints
- Update dependencies to compatible versions
- Use `uv lock --upgrade` to refresh lock file

#### 4. Model Download Failures

**Symptoms**: HuggingFace model download fails

**Cause**: Network issues or cache problems

**Solution**:
- Clear HuggingFace cache: `rm -rf ~/.cache/huggingface`
- Check internet connectivity
- Verify model names and versions

### Debug Mode

Enable debug logging in GitHub Actions:

```yaml
- name: Debug setup
  run: |
    echo "Python version: $(python --version)"
    echo "UV version: $(uv --version)"
    echo "Environment: ${{ toJson(env) }}"
```

### Cache Issues

If caching causes problems:

1. **Clear all caches**: Delete cache entries in GitHub Actions UI
2. **Force cache refresh**: Update cache keys in workflow
3. **Disable caching temporarily**: Comment out cache steps for debugging

## Repository Cleanup

A separate **Repository Cleanup** workflow reduces GitHub Actions storage usage:

- **Triggers**: After Python CI completes on main, or manually via `workflow_dispatch`
- **Branch cleanup**: Deletes merged remote/local branches (feature/*, task/*)
- **Workflow run cleanup**:
  1. Runs from deleted branches
  2. PR ref runs (refs/pull/*)
  3. Obsolete queued/waiting runs (older than 7 days)
  4. Superseded runs (keeps most recent successful per workflow+branch; keeps failed runs for debugging)

**Manual run**: Actions → Repository Cleanup → Run workflow

## Monitoring and Maintenance

### Regular Checks

1. **Dependency Updates**: Monitor for new versions of critical dependencies
2. **Python Version Support**: Check when Python 3.14 compatibility is available
3. **Workflow Performance**: Monitor job execution times and optimize as needed

### Updating Python Version

When Python 3.14 compatibility is available:

1. Update `pyproject.toml` constraints
2. Update workflow matrix
3. Test locally with new version
4. Update documentation

### Performance Optimization

The workflow is optimized for cached runs:

- **astral-sh/setup-uv**: Replaces manual curl install and separate cache step. Caches both Python and UV dependencies.
- **Shallow checkout** (`fetch-depth: 1`): Faster Git clone.
- **Parallelism**: lint, model-download, and security run in parallel after setup; test jobs run in parallel after model-download.
- **Smart cache invalidation**: UV cache invalidates on lock file changes; HF cache invalidates only on model setup script changes, not on application code changes.

Monitor cache hit rates and job durations in the Actions UI.

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [pypika Issue Tracker](https://github.com/kayak/pypika)

## Code Files

- [.github/workflows/python-ci.yml](../../.github/workflows/python-ci.yml) - Main GitHub Actions workflow configuration
- [.github/workflows/cleanup.yml](../../.github/workflows/cleanup.yml) - Repository and workflow run cleanup
- [scripts/cleanup-github-actions.sh](../../scripts/cleanup-github-actions.sh) - Workflow run cleanup script
- [scripts/cleanup-merged-branches.sh](../../scripts/cleanup-merged-branches.sh) - Merged branch cleanup script
- [tests/ci/test_github_actions_setup.py](../../tests/ci/test_github_actions_setup.py) - CI setup validation tests
- [pyproject.toml](../../pyproject.toml) - Project configuration with Python version constraints
- [scripts/setup_embedding_models.py](../../scripts/setup_embedding_models.py) - Embedding model setup script
