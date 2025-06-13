# CODEX.md

## Introduction

This document provides an extensive description of OpenAI Codex and its application within our project to enhance coding productivity and efficiency.

## What is OpenAI Codex?

OpenAI Codex is an advanced AI system capable of translating natural language into code. It is built on the GPT-3 model and is designed to assist developers by providing intelligent code suggestions, automating repetitive tasks, and improving overall coding efficiency.

## Key Features

- **Natural Language Processing**: Codex can understand and interpret natural language instructions, making it easier for developers to communicate their coding needs.
- **Code Generation**: It can generate code snippets in various programming languages, reducing the time spent on manual coding.
- **Error Detection**: Codex can identify and suggest fixes for common coding errors, enhancing code quality.
- **Integration**: Easily integrates with existing development environments and workflows.

## Implementation in Our Project

- **Branch Management**: Codex is utilized on the main branch to ensure consistency and avoid conflicts.
- **Commit Strategy**: Supports multiple commits for separate smaller tasks, maintaining a clear and organized commit history.
- **GitHub Actions**: Ensures all actions pass, including ruff linting and fixing. Adjustments may be needed in `pyproject.toml` for certain rules.
- **Documentation**: Regular updates to project progress reports in markdown files like STORY-xxx, TASK-xxx, FEAT-xxx.
- **Package Management**: Utilizes 'uv add -U {package}' for package installation and updates, ensuring 'uv' is installed and used.
- **Testing**: All pytests must pass, with a preference for code coverage measurements.

## Codex Workspace Management

### Codex Environment Setup

Codex workspaces require proper initialization with uv and project dependencies. This section provides both automated and manual setup procedures.

#### Automated Setup (Recommended)

Use the provided setup script for quick and reliable environment initialization:

```bash
# Make the script executable (first time only)
chmod +x scripts/setup_codex.sh

# Run standard setup
./scripts/setup_codex.sh

# Run setup with clean environment
./scripts/setup_codex.sh --clean

# Run setup without test verification (faster)
./scripts/setup_codex.sh --skip-tests

# Show help
./scripts/setup_codex.sh --help
```

**The setup script performs these steps:**

1. **Environment Check**: Verifies Codex environment and project structure
2. **uv Installation**: Installs uv at system level if not present
3. **Python Setup**: Ensures compatible Python version (3.12+)
4. **Environment Cleaning**: Optionally removes existing virtual environment
5. **Dependency Installation**: Installs all project dependencies from `pyproject.toml`
6. **Verification**: Tests critical dependencies (especially `httpx`)
7. **Test Run**: Validates setup by running the test suite
8. **Environment Report**: Shows installation status and next steps

#### Manual Setup Procedures

If the automated script fails or you prefer manual setup:

##### 1. Install uv (System Level)

```bash
# Using curl (preferred)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Using wget (alternative)
wget -qO- https://astral.sh/uv/install.sh | sh

# Add to PATH for current session
export PATH="$HOME/.cargo/bin:$PATH"

# Add to shell profile for persistence
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

##### 2. Setup Python Environment

```bash
# Install Python 3.12 via uv (recommended)
uv python install 3.12

# Pin Python version for project
uv python pin 3.12

# Verify Python version
python3 --version
```

##### 3. Clean Previous Environment (if needed)

```bash
# Remove virtual environment
rm -rf .venv

# Remove lock file
rm -f uv.lock

# Clean uv cache
uv cache clean --all
```

##### 4. Install Project Dependencies

```bash
# Create virtual environment and install dependencies
uv sync --verbose

# Verify critical dependencies
uv pip list | grep -E "(httpx|fastapi|pytest)"

# Test httpx specifically (original issue)
uv run python -c "import httpx; print(f'httpx version: {httpx.__version__}')"
```

##### 5. Verify Installation

```bash
# Run quick test
uv run pytest --version

# Run full test suite
uv run pytest

# Check all available scripts
grep '\[project.scripts\]' -A 10 pyproject.toml
```

#### Codex Admin Setup Instructions

**For Codex Administrators setting up workspaces:**

##### Container Image Requirements

Ensure the Codex container includes:

```dockerfile
# Dockerfile additions for Codex
# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv at system level
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy project files
COPY . .

# Run setup script
RUN chmod +x scripts/setup_codex.sh && \
    ./scripts/setup_codex.sh --skip-tests
```

##### Workspace Configuration

Configure Codex workspace with these settings:

```yaml
# .codex/workspace.yml
version: "1"
workspace:
  name: "on_prem_rag"
  python_version: "3.12"
  setup_script: "scripts/setup_codex.sh"

environment:
  variables:
    UV_CACHE_DIR: "/workspace/.uv_cache"
    PYTHONPATH: "/workspace/src"

dependencies:
  system:
    - curl
    - wget
    - git
    - build-essential

startup_commands:
  - "chmod +x scripts/setup_codex.sh"
  - "./scripts/setup_codex.sh --clean"
```

##### Network and Security

Configure network access for dependency installation:

```bash
# Allow PyPI access
curl -I https://pypi.org/simple/

# Allow GitHub access for uv installation
curl -I https://github.com/astral-sh/uv

# Test DNS resolution
nslookup pypi.org
```

###### Allowed Domains

Codex workspaces may restrict outbound network access. Allow these domains to
enable documentation lookups and model downloads:

- `pypi.org` - Python packages
- `huggingface.co` - embedding and model downloads
- `github.com` - documentation and setup scripts
- `openai.com` - API references

Without access to these domains, tests marked with `internet` will be
skipped.

#### Troubleshooting Setup Issues

##### uv Installation Fails

```bash
# Check network connectivity
curl -I https://astral.sh/

# Check available space
df -h

# Manual installation
mkdir -p ~/.cargo/bin
wget https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz
tar -xzf uv-*.tar.gz -C ~/.cargo/bin/
export PATH="$HOME/.cargo/bin:$PATH"
```

##### Python Version Issues

```bash
# Check available Python versions
uv python list

# Install specific version
uv python install 3.12.5

# Check system Python
which python3
python3 --version
```

##### Dependency Installation Fails

```bash
# Check disk space
df -h

# Clear all caches
uv cache clean --all
rm -rf ~/.cache/pip
rm -rf ~/.cache/uv

# Verbose installation
uv sync --verbose --no-cache

# Check specific package
uv add httpx --verbose
```

##### Network/Proxy Issues

```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Test connectivity
curl -I https://pypi.org/simple/

# Use alternative index
uv sync --index-url https://pypi.org/simple/
```

#### First-Time Setup Checklist

**For new Codex users:**

- [ ] Run setup script: `./scripts/setup_codex.sh`
- [ ] Verify uv installation: `uv --version`
- [ ] Check Python version: `python3 --version`
- [ ] Verify httpx: `uv run python -c "import httpx"`
- [ ] Run tests: `uv run pytest -q`
- [ ] Check available scripts: `grep '\[project.scripts\]' -A 5 pyproject.toml`

**Expected output after successful setup:**

```
✓ httpx: 0.28.1
✓ fastapi: 0.104.0+
✓ pytest: 8.4.0+
✓ uvicorn: 0.24.0+
✓ chromadb: 0.4.0+
```

**Test Organization:**
The project uses pytest markers to categorize tests:

- **Fast tests**: Complete in <10 seconds, suitable for quick verification
- **Slow tests**: Take >10 seconds, involve model loading, PDF processing, etc.
- **Requires internet**: Perform network downloads. Run with `--run-internet` to enable.

**Testing Commands:**

```bash
# Run only fast tests (used by setup script)
uv run pytest -m "not slow"

# Run all tests
uv run pytest

# Run only slow tests
uv run pytest -m slow

# Run tests with coverage
uv run pytest --cov=src/backend --cov-report=term
```

**If setup fails:**

1. Check the troubleshooting section above
2. Run `./scripts/setup_codex.sh --clean` to reset
3. Contact Codex admin with error logs
4. Escalate to infrastructure team if needed

#### Local Testing (Windows)

For developers working on Windows who want to test the setup process locally:

```powershell
# Run Windows version of setup script
.\scripts\setup_codex.ps1

# Run with clean environment
.\scripts\setup_codex.ps1 -Clean

# Run without tests (faster)
.\scripts\setup_codex.ps1 -SkipTests

# Show help
.\scripts\setup_codex.ps1 -Help
```

**Note**: The PowerShell script (`setup_codex.ps1`) is for local Windows testing only. The actual Codex environment uses the Bash script (`setup_codex.sh`).

#### Quick Reference Guide

**For New Codex Users:**

```bash
# Standard setup (run this first)
./scripts/setup_codex.sh
```

**For Troubleshooting:**

```bash
# Clean setup (if standard fails)
./scripts/setup_codex.sh --clean

# Manual verification
uv --version
uv pip list | grep httpx
uv run pytest -q
```

**For Codex Admins:**

```bash
# Container setup
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Project setup
chmod +x scripts/setup_codex.sh
./scripts/setup_codex.sh --clean --skip-tests
```

### Dependency Management in Codex Environments

Codex workspaces are containerized environments that require proper dependency synchronization when `pyproject.toml` changes are made. Unlike local development environments, Codex requires explicit steps to update dependencies.

#### Common Dependency Issues

**Symptom**: `ModuleNotFoundError` in Codex workspace that doesn't occur locally
**Root Cause**: Dependencies added to local environment but not properly declared in `pyproject.toml`, or Codex workspace hasn't synced updated dependencies

**Example Error**:

```
E   ModuleNotFoundError: No module named 'httpx'
```

#### User-Level Troubleshooting

When encountering missing dependency errors in Codex:

1. **Verify Dependency Declaration**

   ```bash
   # Check if package is declared in pyproject.toml
   grep -i "package-name" pyproject.toml
   ```

2. **Force Dependency Sync**

   ```bash
   # Standard sync (try this first)
   uv sync

   # Force reinstall if standard sync fails
   uv sync --force-reinstall
   ```

3. **Clear Cache and Rebuild**

   ```bash
   # Clear uv cache
   uv cache clean

   # Sync dependencies
   uv sync
   ```

4. **Complete Environment Rebuild**

   ```bash
   # Remove virtual environment
   rm -rf .venv

   # Rebuild from scratch
   uv sync
   ```

5. **Verify Installation**

   ```bash
   # Check if package is now installed
   uv pip list | grep package-name

   # Test with pytest
   uv run pytest -q
   ```

#### Admin-Level Procedures

**For Codex Administrators**: When users report persistent dependency issues that user-level troubleshooting cannot resolve:

##### Workspace Validation

1. **Check Workspace Configuration**

   ```bash
   # Verify uv version and configuration
   uv --version
   uv config list

   # Check Python version consistency
   python --version
   uv python list
   ```

2. **Validate pyproject.toml Integrity**

   ```bash
   # Validate project configuration
   uv tree

   # Check for conflicts
   uv sync --dry-run
   ```

3. **Environment Health Check**

   ```bash
   # Check virtual environment status
   ls -la .venv/

   # Verify package installation paths
   uv pip show package-name
   ```

##### Workspace Reconstruction

If validation reveals corruption or persistent issues:

1. **Backup Current State**

   ```bash
   # Backup current environment info
   uv pip list > current_packages.txt
   uv pip freeze > current_freeze.txt
   ```

2. **Complete Workspace Reset**

   ```bash
   # Remove all cached data
   uv cache clean --all

   # Remove virtual environment
   rm -rf .venv

   # Remove any lock files if needed
   rm -f uv.lock

   # Rebuild from pyproject.toml
   uv sync --reinstall
   ```

3. **Verify Reconstruction**

   ```bash
   # Compare package lists
   uv pip list > new_packages.txt
   diff current_packages.txt new_packages.txt

   # Run full test suite
   uv run pytest
   ```

##### System-Level Issues

For container or system-level problems:

1. **Container Health Check**

   ```bash
   # Check container resources
   df -h
   free -m

   # Check for permission issues
   ls -la /workspace/
   whoami
   ```

2. **Network Connectivity**

   ```bash
   # Test PyPI connectivity
   curl -I https://pypi.org/simple/

   # Test DNS resolution
   nslookup pypi.org
   ```

3. **Python Environment Validation**

   ```bash
   # Check Python installation
   which python
   python -c "import sys; print(sys.path)"

   # Verify pip/uv functionality
   python -m pip --version
   uv --version
   ```

#### Prevention Guidelines

To prevent dependency issues in Codex workspaces:

1. **Development Workflow**

   - Always use `uv add package-name` instead of `pip install`
   - Verify `pyproject.toml` is updated after adding dependencies
   - Test in clean environment before deploying to Codex

2. **Code Review Checklist**

   - [ ] All imported packages declared in `pyproject.toml`
   - [ ] No `pip install` commands in development notes
   - [ ] `uv.lock` file updated (if tracked)
   - [ ] Tests pass in fresh environment

3. **Documentation Updates**
   - Update this file when new Codex-specific issues are discovered
   - Document any admin procedures in this section
   - Keep troubleshooting steps current with uv version updates

#### Escalation Path

1. **User Level**: Follow user-level troubleshooting steps
2. **Team Level**: Consult with team members who have Codex experience
3. **Admin Level**: Contact Codex administrators with specific error logs
4. **System Level**: Escalate to infrastructure team for container/network issues

Provide the following information when escalating:

- Exact error messages and stack traces
- Steps already attempted
- `uv --version` and `python --version` output
- Contents of `pyproject.toml` dependencies section
- Output of `uv pip list`

## Benefits

- **Increased Productivity**: Automates repetitive tasks and provides quick code suggestions, allowing developers to focus on more complex problems.
- **Improved Code Quality**: Offers intelligent suggestions and error detection, leading to cleaner and more efficient code.
- **Seamless Integration**: Works well with existing tools and workflows, minimizing disruption.

## Conclusion

The integration of OpenAI Codex into our project is aimed at optimizing development workflows, reducing manual coding efforts, and maintaining high code quality standards. By adhering to the outlined guidelines and regularly updating Codex, we can ensure its effective use in our project.

Proper dependency management in Codex environments is critical for maintaining consistent development experiences across all team members and avoiding time-consuming debugging sessions.

## References

- [OpenAI Codex Documentation](https://openai.com/blog/openai-codex/)
- [AGENTS.md](../AGENTS.md) - Codex integration workflow guidelines
- [uv Documentation](https://docs.astral.sh/uv/) - Dependency management reference
- [Dependency Management Rule](.cursor/rules/dependency-management.mdc) - Project-specific dependency guidelines

## Code Files

Intentionally left empty - no direct code dependencies. This document describes development methodology and AI assistance integration rather than specific implementation code.
