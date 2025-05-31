# Task 1.1: Initialize Project Environment

## Context from Goal 1

This task establishes the foundational Python development environment for our on-premises RAG solution. The environment must support modern Python development practices while ensuring reproducible builds and code quality that meets enterprise standards.

## Problem Statement

We need a robust Python development environment that:
- Supports fast, reliable dependency management
- Enforces code quality standards automatically
- Integrates with our containerized deployment strategy
- Minimizes dependency conflicts and security vulnerabilities

## Technology Considerations

### Dependency Management Options

#### Option 1: pip + venv (Traditional)
- **Pros**: Universal compatibility, simple setup
- **Cons**: Slow dependency resolution, no lock file format
- **Use Case**: Legacy projects, simple scripts

#### Option 2: Poetry
- **Pros**: Excellent dependency management, good for libraries
- **Cons**: Slower than modern alternatives, complex for simple projects
- **Use Case**: Python library development

#### Option 3: uv (Chosen)
- **Pros**: 10-100x faster than pip, Rust-based reliability, pip-compatible
- **Cons**: Newer tool, smaller community
- **Use Case**: Modern Python applications requiring speed

### Code Quality Tools

#### Option 1: flake8 + black + isort
- **Pros**: Mature ecosystem, widely adopted
- **Cons**: Multiple tools, slower execution
- **Use Case**: Existing projects with established workflows

#### Option 2: ruff (Chosen)
- **Pros**: 10-100x faster, combines multiple tools, Rust-based
- **Cons**: Newer tool, some advanced rules still developing
- **Use Case**: New projects prioritizing speed and simplicity

### Decision: uv + ruff + pre-commit

**Rationale**: Prioritize development speed and modern tooling while maintaining compatibility with traditional Python workflows. The speed benefits compound over the project lifecycle.

## Implementation Steps

### Step 1: Install Core Tools

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Step 2: Initialize Python Project

```bash
# Create project structure
mkdir -p src/rag_system tests docs

# Initialize Python project with uv
uv init --python 3.11

# Create virtual environment
uv venv .venv

# Activate environment (Windows)
.venv\Scripts\activate

# Activate environment (Unix)
source .venv/bin/activate
```

### Step 3: Configure Dependencies

Create `pyproject.toml`:

```toml
[project]
name = "on-prem-rag"
version = "0.1.0"
description = "On-premises RAG solution for enterprise document analysis"
requires-python = ">=3.10"
authors = [
    {name = "Your Organization", email = "tech@yourorg.com"}
]

dependencies = [
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "chromadb>=0.4.0",
    "ollama>=0.1.7",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "streamlit>=1.28.0",
    "pypdf>=3.17.0",
    "python-docx>=1.1.0",
    "python-multipart>=0.0.6",
    "sentence-transformers>=2.2.2",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.6",
    "pre-commit>=3.5.0",
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.9.0",
]

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings  
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

[tool.ruff.per-file-ignores]
"tests/*" = ["E501"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Step 4: Install Dependencies

```bash
# Install production dependencies
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### Step 5: Configure Pre-commit

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
        
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
```

Install pre-commit hooks:

```bash
pre-commit install
```

### Step 6: Verify Setup

Test the environment:

```python
# test_environment.py
"""Quick environment verification."""

def test_imports():
    """Test that key dependencies can be imported."""
    try:
        import langchain
        import chromadb
        import fastapi
        import streamlit
        print("✅ All core dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_tools():
    """Test development tools."""
    import subprocess
    
    tools = ["ruff", "pre-commit"]
    for tool in tools:
        try:
            result = subprocess.run([tool, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {tool}: {result.stdout.strip()}")
            else:
                print(f"❌ {tool}: Command failed")
        except FileNotFoundError:
            print(f"❌ {tool}: Not found in PATH")

if __name__ == "__main__":
    test_imports()
    test_tools()
```

Run verification:

```bash
python test_environment.py
```

## Common Issues and Solutions

### Issue 1: uv Not Found
**Solution**: Ensure uv is in your PATH. Restart terminal after installation.

### Issue 2: Virtual Environment Activation Fails
**Solution**: Use full path to activation script:
```bash
# Windows
C:\path\to\project\.venv\Scripts\activate

# Unix
/path/to/project/.venv/bin/activate
```

### Issue 3: Pre-commit Hooks Fail
**Solution**: Run hooks manually to see detailed errors:
```bash
pre-commit run --all-files
```

## Definition of Done

### Environment Setup
- [ ] uv installed and functional
- [ ] Python virtual environment created and activated
- [ ] All dependencies installed without conflicts
- [ ] Development tools (ruff, pre-commit) configured

### Code Quality
- [ ] Pre-commit hooks installed and passing
- [ ] Ruff configuration working correctly
- [ ] Test environment verification script passes

### Documentation
- [ ] pyproject.toml properly configured
- [ ] README updated with setup instructions
- [ ] Development workflow documented

### Verification
- [ ] Clean git status after setup
- [ ] All imports working correctly
- [ ] No linting errors on existing code

## Next Steps

1. Proceed to [Task 1.2: Docker Configuration](task-1-2-docker.md)
2. Test dependency installation on clean system
3. Document any organization-specific setup requirements

## References

- [uv Documentation](https://github.com/astral-sh/uv)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [pre-commit Documentation](https://pre-commit.com/)
- [Python Packaging User Guide](https://packaging.python.org/) 