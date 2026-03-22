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

1. **Verify CI base (GHCR)**: Pulls the shared container image before any job uses `container:` (fails fast with a job summary if auth or tag is wrong)
2. **Setup Job**: Installs dependencies and warms the UV cache
3. **Lint Job**: Runs code quality checks (depends on setup)
4. **Model Download Job**: Downloads embedding models (depends on setup)
5. **Unit Tests**: Fast tests in the CI base container (depends on setup + verify; does not wait for model-download — uses cache restore + offline-friendly ensure step)
6. **Performance Tests**: Slow tests in the CI base container, conditional execution
7. **Integration Tests**: Internet-dependent tests in the CI base container, conditional execution
8. **Security Scan**: Vulnerability scanning (depends on setup; runs on the default runner, not the CI base image)
9. **CI Summary**: Aggregates results from all jobs

### Shared CI base image (GHCR)

Unit, performance, and integration test jobs run inside a pre-built image maintained in **[pkuppens/pkuppens](https://github.com/pkuppens/pkuppens)** (reuse across your repos).

- **Default image:** `ghcr.io/pkuppens/pkuppens/ci-base-3.12:latest` (see [package page](https://github.com/pkuppens/pkuppens/pkgs/container/pkuppens%2Fci-base-3.12)). Hugging Face models for offline tests come from **`model-download`** + **`actions/cache`** and from **`setup_embedding_models.py --ci`** in container jobs when the cache misses. Optional **[ci-hf-base-3.12](https://github.com/pkuppens/pkuppens/pkgs/container/pkuppens%2Fci-hf-base-3.12)** can be selected via **`CI_BASE_IMAGE`** or **`CI_INTEGRATION_IMAGE`** only if it matches your **chromadb / uv** stack (the slim ci-base image is the default that matches this repo’s CI).
- **Override:** set repository **Actions variable** `CI_BASE_IMAGE` to another tag or image (workflow `env` uses it when non-empty)
- **Integration-only image (optional):** set **`CI_INTEGRATION_IMAGE`** when **test-integration** should use a **different** image than unit/performance (for example an HF-baked **`ci-hf-base-3.12`** while **`CI_BASE_IMAGE`** stays **`ci-base-3.12`**). When unset, it falls back to the same value as `CI_BASE_IMAGE`. The **Verify GHCR CI base image** job pulls **both** images when they differ.
- **Private package:** if `GITHUB_TOKEN` cannot pull from another repo’s package, add repository secret **`GHCR_READ_TOKEN`** (PAT with `read:packages`) **or** grant this repository access to the package under **Package settings → Manage actions access**

Local smoke test:

```bash
docker pull ghcr.io/pkuppens/pkuppens/ci-base-3.12:latest
```

If the **Verify GHCR CI base image** job fails, open that job’s **summary** for copy-paste fix hints (login vs 404 vs permissions).

Container test jobs run **`apt-get install build-essential`** (or Alpine `apk` equivalents) before `uv sync`, because slim base images may not include `g++` and some dependencies (for example **annoy**) build from source.

### Model Download Only (Manual)

The **Model Download Only** workflow (`.github/workflows/model-download-only.yml`) runs the model-download job in isolation. Use it for fast iteration when debugging model-download CI failures (~4 min vs full pipeline). Follows the Cleanup pattern; subject to `cleanup-github-actions.sh`. On success, uploads `huggingface-models` artifact for debugging.

**Trigger**: Actions → Model Download Only → Run workflow (select branch)

### Cloud LLM Test (Manual)

The **Cloud LLM Test** workflow (`.github/workflows/cloud-llm.yml`) runs separately and is triggered manually only. Use it when Cloud LLM code (e.g. Gemini, llm_config) is changed. If `GEMINI_API_KEY` is not set, the test skips gracefully. Trigger via Actions → Cloud LLM Test → Run workflow.

### Environment Variables

Per-step shell exports for HuggingFace model caching (do **not** set `HF_HOME` at workflow root to `github.workspace` — it conflicts with `~/.cache` used by `actions/cache`):

```yaml
# Inside a run: step (model-download, test-unit, etc.)
run: |
  export HF_HOME=$HOME/.cache/huggingface
  export TRANSFORMERS_CACHE=$HOME/.cache/huggingface/hub
  export SENTENCE_TRANSFORMERS_HOME=$HOME/.cache/huggingface/sentence_transformers
```

For model-download steps, additional env vars prevent encoding and progress-bar issues in CI:

```yaml
env:
  PYTHONIOENCODING: utf-8
  HF_HUB_DISABLE_PROGRESS_BARS: "1"
  LANG: C.UTF-8
  LC_ALL: C.UTF-8
```

### Caching Strategy

The workflow uses multiple cache layers:

1. **Python and uv** (via `astral-sh/setup-uv`): Python installs and UV dependency cache. Invalidates when `uv.lock` or `pyproject.toml` changes. First runs are slower; cached runs skip Python/UV install.
2. **HuggingFace Models**: Cached based on `pyproject.toml` and `uv.lock` hash—invalidates when deps change. Setup script tweaks do not invalidate. Restore-keys allow fallback to older cache. Container **test-unit** and **test-performance** jobs also run **`scripts/setup_embedding_models.py --ci`** after cache restore (network allowed for that step only) so models exist under `$HOME/.cache/huggingface` when cache restore misses or the base image layout differs.
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

| Job              | Timeout | Rationale                                                       |
| ---------------- | ------- | --------------------------------------------------------------- |
| test-unit        | 30 min  | Temporary; reduce once runs stabilize. Includes setup + pytest. |
| test-performance | 10 min  | Slow tests; sequential execution.                               |
| test-integration | 15 min  | Internet-dependent; sequential execution.                       |

## Coverage Reports

After each successful Python CI run, the `test-unit` job uploads a `coverage-reports` artifact containing per-file coverage and JUnit results.

### Downloading via gh CLI (recommended)

The Artifacts section on the run page may not be visible in some account/org configurations. Use `gh run download` instead:

```bash
# Get RUN_ID from: Actions → select run → URL contains /runs/RUN_ID
# Or: gh run list --workflow "Python CI" --limit 5

gh run download <RUN_ID> --name coverage-reports --dir tmp/coverage-reports
```

After download, open `tmp/coverage-reports/htmlcov/index.html` in a browser for the per-file coverage report.

### Downloading via GitHub Web UI

1. Go to **Actions** → select the workflow run
2. Scroll to the **Artifacts** section at the bottom
3. Click **coverage-reports** to download the zip
4. Extract and open `htmlcov/index.html` for per-file coverage

### Artifact contents

| File/folder             | Purpose                                  |
| ----------------------- | ---------------------------------------- |
| `htmlcov/`              | Per-file HTML coverage (open index.html) |
| `coverage.xml`          | Raw coverage data (for tools)            |
| `test-results-unit.xml` | JUnit test results                       |

### PR comments

Coverage is posted as a PR comment only when coverage < 60% (to reduce notification noise). Coverage is always available in the job summary and artifacts.

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
- **Branch cleanup**: Deletes merged remote/local branches (feature/_, task/_)
- **When cleanup runs**: The workflow only proceeds if the triggering Python CI run succeeded and there are no other **Python CI** runs for the same commit (`head_sha`) still in progress. Otherwise it skips until those runs finish (or you run cleanup manually).
- **Duplicate CI on the same branch**: **Python CI** already uses a workflow `concurrency` group with `cancel-in-progress: true` (see `.github/workflows/python-ci.yml`), so a newer push cancels an older in-progress run on the same ref. The cleanup script does **not** call `gh run cancel`; it only deletes **completed** runs per the retention rules below.
- **Workflow run cleanup** (same order as `scripts/cleanup-github-actions.sh`):
  1. Obsolete queued/waiting runs (older than 7 days)
  2. PR ref runs (`refs/pull/*`)
  3. Runs for deleted branches
  4. Superseded runs (per active workflow+branch: keep the latest **success**; keep completed failures **after** that success for debugging; delete older completed passes and older completed failures)
  5. Extra **Repository Cleanup** workflow runs (same keep rules as step 4, dedicated fetch)
  6. Orphaned runs (workflow file removed from the repo but runs still exist)
- **In-flight runs**: Steps that apply supersession (4 and 5a) never delete runs whose `status` is not `completed`.

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
- **Parallelism**: lint, model-download, security, and **test-unit** (after setup + verify) run in overlapping waves; performance/integration still wait on model-download + verify.
- **Smart cache invalidation**: UV cache invalidates on lock file changes; HF cache invalidates on `pyproject.toml`/`uv.lock` changes (dep-driven), not on setup script or application code changes.

Monitor cache hit rates and job durations in the Actions UI.

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [UV Package Manager](https://github.com/astral-sh/uv)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [pypika Issue Tracker](https://github.com/kayak/pypika)

## Code Files

- [.github/workflows/python-ci.yml](../../.github/workflows/python-ci.yml) - Main GitHub Actions workflow configuration
- [.github/workflows/model-download-only.yml](../../.github/workflows/model-download-only.yml) - Isolated model-download for fast iteration
- [.github/workflows/cleanup.yml](../../.github/workflows/cleanup.yml) - Repository and workflow run cleanup
- [scripts/cleanup-github-actions.sh](../../scripts/cleanup-github-actions.sh) - Workflow run cleanup script
- [scripts/cleanup-merged-branches.sh](../../scripts/cleanup-merged-branches.sh) - Merged branch cleanup script
- [tests/ci/test_github_actions_setup.py](../../tests/ci/test_github_actions_setup.py) - CI setup validation tests
- [pyproject.toml](../../pyproject.toml) - Project configuration with Python version constraints
- [scripts/setup_embedding_models.py](../../scripts/setup_embedding_models.py) - Embedding model setup script
