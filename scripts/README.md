# Scripts Directory

This directory contains setup and utility scripts for the on_prem_rag project.

## Setup Scripts

### setup_codex.sh (Linux/Codex)

The primary setup script for Codex environments and Linux systems.

**Purpose**: Automatically sets up the Codex workspace with uv and project dependencies at system level.

**Usage**:

```bash
# Make executable (first time only)
chmod +x scripts/setup_codex.sh

# Standard setup
./scripts/setup_codex.sh

# Clean environment setup
./scripts/setup_codex.sh --clean

# Setup without test verification
./scripts/setup_codex.sh --skip-tests

# Show help
./scripts/setup_codex.sh --help
```

**What it does**:

1. Checks environment and project structure
2. Installs uv at system level if not present
3. Sets up Python 3.12+ environment
4. Optionally cleans existing virtual environment
5. Installs all project dependencies from pyproject.toml
6. Verifies critical dependencies (especially httpx)
7. Runs test suite to validate setup
8. Displays environment information and next steps

### setup_codex.ps1 (Windows)

PowerShell version for local Windows testing.

**Purpose**: Allows Windows developers to test the setup process locally before deploying to Codex.

**Usage**:

```powershell
# Standard setup
.\scripts\setup_codex.ps1

# Clean environment setup
.\scripts\setup_codex.ps1 -Clean

# Setup without test verification
.\scripts\setup_codex.ps1 -SkipTests

# Show help
.\scripts\setup_codex.ps1 -Help
```

**Note**: This is for local testing only. Production Codex environments should use `setup_codex.sh`.

## When to Use These Scripts

### For New Codex Users

Run the setup script immediately after accessing a new Codex workspace:

```bash
./scripts/setup_codex.sh
```

### For Dependency Issues

When encountering `ModuleNotFoundError` (like the httpx issue):

```bash
./scripts/setup_codex.sh --clean
```

### For Codex Administrators

When setting up new workspaces or containers:

```bash
# Install uv system-wide first
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Then run project setup
chmod +x scripts/setup_codex.sh
./scripts/setup_codex.sh --clean --skip-tests
```

### For Local Development Testing

Before pushing changes that affect dependencies:

```powershell
# On Windows
.\scripts\setup_codex.ps1 -Clean
```

## Troubleshooting

If the setup scripts fail:

1. **Check Prerequisites**:

   - Network connectivity to PyPI and GitHub
   - Sufficient disk space (check with `df -h`)
   - Proper permissions in the workspace

2. **Common Issues**:

   - **Network errors**: Check proxy settings or use alternative installation methods
   - **Permission errors**: Ensure you have write access to the workspace
   - **Python version issues**: Let uv manage Python installation

3. **Manual Recovery**:

   ```bash
   # Remove everything and start fresh
   rm -rf .venv uv.lock
   uv cache clean --all
   ./scripts/setup_codex.sh --clean
   ```

4. **Get Help**:
   - Check [docs/technical/CODEX.md](../docs/technical/CODEX.md) for detailed troubleshooting
   - Contact Codex administrators with error logs
   - Escalate to infrastructure team for system-level issues

## Script Development

When modifying these scripts:

1. **Test Locally First**: Use the PowerShell version on Windows to test logic changes
2. **Update Both Versions**: Keep bash and PowerShell scripts functionally equivalent
3. **Update Documentation**: Update CODEX.md and this README when adding features
4. **Test in Clean Environment**: Verify scripts work in fresh Codex workspaces

## Dependencies

These scripts require:

- **Linux/Codex**: bash, curl or wget, basic Unix utilities
- **Windows**: PowerShell 5.1+, optionally winget for uv installation
- **Network**: Access to pypi.org, github.com, astral.sh

## Related Documentation

- [CODEX.md](../docs/technical/CODEX.md) - Complete Codex workspace management guide
- [AGENTS.md](../AGENTS.md) - Development workflow and dependency management
- [README.md](../README.md) - Project overview and setup instructions
- [.cursor/rules/dependency-management.mdc](../.cursor/rules/dependency-management.mdc) - Dependency management rules
