#!/bin/bash
# setup_codex.sh - Codex Environment Setup Script
# This script sets up the Codex workspace with uv and project dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in a supported environment
check_environment() {
    log_info "Checking environment..."
    
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_warning "This script is designed for Linux environments (Codex)"
        log_info "Detected OS: $OSTYPE"
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]]; then
        log_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi
    
    log_success "Environment check passed"
}

# Install uv if not present
install_uv() {
    log_info "Checking for uv installation..."
    
    if command -v uv &> /dev/null; then
        local uv_version=$(uv --version)
        log_success "uv is already installed: $uv_version"
        return 0
    fi
    
    log_info "Installing uv..."
    
    # Install uv using the official installer
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget &> /dev/null; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        log_error "Neither curl nor wget is available. Cannot install uv."
        exit 1
    fi
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Verify installation
    if command -v uv &> /dev/null; then
        local uv_version=$(uv --version)
        log_success "uv installed successfully: $uv_version"
    else
        log_error "uv installation failed"
        exit 1
    fi
}

# Setup Python environment
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Check required Python version from pyproject.toml
    local required_python=$(grep -E "requires-python.*=" pyproject.toml | sed 's/.*>=\([0-9.]*\).*/\1/')
    if [[ -n "$required_python" ]]; then
        log_info "Project requires Python >= $required_python"
    fi
    
    # Check current Python version
    local python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "Not found")
    log_info "Current Python version: $python_version"
    
    # Install Python if needed using uv
    if [[ "$python_version" == "Not found" ]] || ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
        log_info "Installing/updating Python using uv..."
        uv python install 3.12
        uv python pin 3.12
    fi
    
    log_success "Python environment ready"
}

# Clean existing environment
clean_environment() {
    log_info "Cleaning existing environment..."
    
    if [[ -d ".venv" ]]; then
        log_info "Removing existing virtual environment..."
        rm -rf .venv
    fi
    
    if [[ -f "uv.lock" ]]; then
        log_info "Removing existing lock file..."
        rm -f uv.lock
    fi
    
    # Clean uv cache
    if command -v uv &> /dev/null; then
        log_info "Cleaning uv cache..."
        uv cache clean --all || log_warning "Failed to clean cache (may not exist)"
    fi
    
    log_success "Environment cleaned"
}

# Install project dependencies
install_dependencies() {
    log_info "Installing project dependencies..."
    
    # Create virtual environment and install dependencies
    log_info "Creating virtual environment and installing dependencies..."
    uv sync --verbose
    
    # Verify critical dependencies
    log_info "Verifying critical dependencies..."
    
    # Check for httpx specifically (the dependency that caused the original issue)
    if uv pip list | grep -q "httpx"; then
        log_success "httpx dependency verified"
    else
        log_error "httpx dependency missing - this may cause test failures"
        exit 1
    fi
    
    # Check for other critical packages
    local critical_packages=("fastapi" "pytest" "uvicorn")
    for package in "${critical_packages[@]}"; do
        if uv pip list | grep -q "$package"; then
            log_success "$package dependency verified"
        else
            log_warning "$package dependency missing"
        fi
    done
    
    log_success "Dependencies installed successfully"
}

# Run tests to verify setup
verify_setup() {
    log_info "Verifying setup with test run..."
    
    # Run a quick test to verify everything works
    if uv run python -c "import httpx; print(f'httpx version: {httpx.__version__}')"; then
        log_success "httpx import test passed"
    else
        log_error "httpx import test failed"
        exit 1
    fi
    
    # Run pytest with a timeout to avoid hanging
    log_info "Running test suite (with 5 minute timeout)..."
    if timeout 300 uv run pytest --tb=short -v tests/ || [[ $? == 124 ]]; then
        if [[ $? == 124 ]]; then
            log_warning "Tests timed out after 5 minutes - this may indicate environment issues"
        else
            log_success "Test suite completed"
        fi
    else
        log_error "Test suite failed"
        log_info "This may be expected if there are test-specific issues unrelated to environment setup"
    fi
}

# Display environment information
show_environment_info() {
    log_info "Environment Information:"
    echo "=========================="
    echo "Python version: $(python3 --version)"
    echo "uv version: $(uv --version)"
    echo "Project root: $(pwd)"
    echo "Virtual environment: $(ls -la .venv 2>/dev/null | head -1 || echo 'Not found')"
    echo ""
    
    log_info "Installed packages:"
    uv pip list | head -20
    if [[ $(uv pip list | wc -l) -gt 20 ]]; then
        echo "... (showing first 20 packages, run 'uv pip list' for full list)"
    fi
    echo ""
    
    log_info "Critical dependencies status:"
    local critical_deps=("httpx" "fastapi" "pytest" "uvicorn" "chromadb")
    for dep in "${critical_deps[@]}"; do
        if uv pip list | grep -q "$dep"; then
            local version=$(uv pip list | grep "$dep" | awk '{print $2}')
            echo "✓ $dep: $version"
        else
            echo "✗ $dep: NOT INSTALLED"
        fi
    done
}

# Main setup function
main() {
    log_info "Starting Codex environment setup..."
    echo "======================================"
    
    # Parse command line arguments
    CLEAN_ENV=false
    SKIP_TESTS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                CLEAN_ENV=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --help)
                echo "Usage: $0 [--clean] [--skip-tests] [--help]"
                echo "  --clean      Clean existing environment before setup"
                echo "  --skip-tests Skip test verification step"
                echo "  --help       Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Execute setup steps
    check_environment
    install_uv
    setup_python_environment
    
    if [[ "$CLEAN_ENV" == true ]]; then
        clean_environment
    fi
    
    install_dependencies
    
    if [[ "$SKIP_TESTS" != true ]]; then
        verify_setup
    fi
    
    show_environment_info
    
    log_success "Codex environment setup completed!"
    echo ""
    log_info "Next steps:"
    echo "1. Run tests: uv run pytest"
    echo "2. Start development server: uv run start-backend"
    echo "3. Check available scripts: grep '\\[project.scripts\\]' -A 10 pyproject.toml"
    echo ""
    log_info "If you encounter issues, check docs/technical/CODEX.md for troubleshooting"
}

# Run main function with all arguments
main "$@" 