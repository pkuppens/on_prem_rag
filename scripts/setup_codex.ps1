# setup_codex.ps1 - Windows/PowerShell version of Codex setup script
# This script provides similar functionality to setup_codex.sh for Windows testing

param(
    [switch]$Clean,
    [switch]$SkipTests,
    [switch]$Help
)

# Colors for output
$Red = [System.ConsoleColor]::Red
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Blue = [System.ConsoleColor]::Blue

function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $host.UI.RawUI.ForegroundColor = $fc
}

function Log-Info($Message) {
    Write-ColorOutput $Blue "[INFO] $Message"
}

function Log-Success($Message) {
    Write-ColorOutput $Green "[SUCCESS] $Message"
}

function Log-Warning($Message) {
    Write-ColorOutput $Yellow "[WARNING] $Message"
}

function Log-Error($Message) {
    Write-ColorOutput $Red "[ERROR] $Message"
}

function Show-Help {
    Write-Output "setup_codex.ps1 - Windows setup script for testing Codex environment setup"
    Write-Output ""
    Write-Output "Usage: .\setup_codex.ps1 [-Clean] [-SkipTests] [-Help]"
    Write-Output "  -Clean      Clean existing environment before setup"
    Write-Output "  -SkipTests  Skip test verification step"
    Write-Output "  -Help       Show this help message"
    Write-Output ""
    Write-Output "Note: This script is for local Windows testing only."
    Write-Output "For actual Codex environments, use scripts/setup_codex.sh"
}

function Test-Environment {
    Log-Info "Checking Windows environment..."
    
    # Check if we're in the right directory
    if (-not (Test-Path "pyproject.toml")) {
        Log-Error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    }
    
    Log-Success "Environment check passed"
}

function Install-Uv {
    Log-Info "Checking for uv installation..."
    
    # Check if uv is available
    try {
        $uvVersion = uv --version 2>$null
        Log-Success "uv is already installed: $uvVersion"
        return
    }
    catch {
        Log-Info "uv not found, attempting installation..."
    }
    
    # Install uv using winget if available
    try {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Log-Info "Installing uv using winget..."
            winget install astral-sh.uv
        }
        else {
            Log-Info "Installing uv using PowerShell script..."
            # Download and install uv
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        }
        
        # Verify installation
        $uvVersion = uv --version 2>$null
        Log-Success "uv installed successfully: $uvVersion"
    }
    catch {
        Log-Error "uv installation failed: $_"
        Log-Info "Please install uv manually:"
        Log-Info "  winget install astral-sh.uv"
        Log-Info "  OR visit: https://astral.sh/uv/getting-started/"
        exit 1
    }
}

function Setup-PythonEnvironment {
    Log-Info "Setting up Python environment..."
    
    # Check required Python version from pyproject.toml
    $requiredPython = Select-String -Path "pyproject.toml" -Pattern 'requires-python.*=' | ForEach-Object { $_.Line } | ForEach-Object { if ($_ -match '>=([0-9.]+)') { $matches[1] } }
    if ($requiredPython) {
        Log-Info "Project requires Python >= $requiredPython"
    }
    
    # Check current Python version
    try {
        $pythonVersion = python --version 2>$null
        Log-Info "Current Python version: $pythonVersion"
    }
    catch {
        Log-Warning "Python not found or not accessible"
    }
    
    # Note: On Windows, uv python management might work differently
    Log-Info "Python environment setup complete (Windows)"
}

function Clear-Environment {
    Log-Info "Cleaning existing environment..."
    
    if (Test-Path ".venv") {
        Log-Info "Removing existing virtual environment..."
        Remove-Item -Recurse -Force ".venv"
    }
    
    if (Test-Path "uv.lock") {
        Log-Info "Removing existing lock file..."
        Remove-Item -Force "uv.lock"
    }
    
    # Clean uv cache
    try {
        Log-Info "Cleaning uv cache..."
        uv cache clean --all
    }
    catch {
        Log-Warning "Failed to clean cache (may not exist)"
    }
    
    Log-Success "Environment cleaned"
}

function Install-Dependencies {
    Log-Info "Installing project dependencies..."
    
    try {
        # Create virtual environment and install dependencies
        Log-Info "Creating virtual environment and installing dependencies..."
        uv sync --verbose
        
        # Verify critical dependencies
        Log-Info "Verifying critical dependencies..."
        
        # Check for httpx specifically
        $httpxCheck = uv pip list | Select-String "httpx"
        if ($httpxCheck) {
            Log-Success "httpx dependency verified: $httpxCheck"
        }
        else {
            Log-Error "httpx dependency missing - this may cause test failures"
            exit 1
        }
        
        # Check for other critical packages
        $criticalPackages = @("fastapi", "pytest", "uvicorn")
        foreach ($package in $criticalPackages) {
            $packageCheck = uv pip list | Select-String $package
            if ($packageCheck) {
                Log-Success "$package dependency verified: $packageCheck"
            }
            else {
                Log-Warning "$package dependency missing"
            }
        }
        
        Log-Success "Dependencies installed successfully"
    }
    catch {
        Log-Error "Dependency installation failed: $_"
        exit 1
    }
}

function Test-Setup {
    Log-Info "Verifying setup with test run..."
    
    try {
        # Test httpx import
        $httpxTest = uv run python -c "import httpx; print(f'httpx version: {httpx.__version__}')"
        if ($httpxTest) {
            Log-Success "httpx import test passed: $httpxTest"
        }
    }
    catch {
        Log-Error "httpx import test failed: $_"
        exit 1
    }
    
    try {
        # Run pytest
        Log-Info "Running test suite..."
        uv run pytest --tb=short -v tests/
        Log-Success "Test suite completed"
    }
    catch {
        Log-Warning "Test suite had issues: $_"
        Log-Info "This may be expected if there are test-specific issues unrelated to environment setup"
    }
}

function Show-EnvironmentInfo {
    Log-Info "Environment Information:"
    Write-Output "=========================="
    
    try {
        $pythonVersion = python --version 2>$null
        Write-Output "Python version: $pythonVersion"
    }
    catch {
        Write-Output "Python version: Not accessible"
    }
    
    try {
        $uvVersion = uv --version 2>$null
        Write-Output "uv version: $uvVersion"
    }
    catch {
        Write-Output "uv version: Not accessible"
    }
    
    Write-Output "Project root: $(Get-Location)"
    
    if (Test-Path ".venv") {
        Write-Output "Virtual environment: Present"
    }
    else {
        Write-Output "Virtual environment: Not found"
    }
    
    Write-Output ""
    
    Log-Info "Installed packages (first 20):"
    try {
        uv pip list | Select-Object -First 20
    }
    catch {
        Write-Output "Could not retrieve package list"
    }
    
    Write-Output ""
    
    Log-Info "Critical dependencies status:"
    $criticalDeps = @("httpx", "fastapi", "pytest", "uvicorn", "chromadb")
    foreach ($dep in $criticalDeps) {
        try {
            $packageInfo = uv pip list | Select-String $dep
            if ($packageInfo) {
                Write-Output "✓ $dep: $($packageInfo.Line.Split()[1])"
            }
            else {
                Write-Output "✗ $dep: NOT INSTALLED"
            }
        }
        catch {
            Write-Output "✗ $dep: CHECK FAILED"
        }
    }
}

# Main function
function Main {
    if ($Help) {
        Show-Help
        return
    }
    
    Log-Info "Starting Windows Codex environment setup (test)..."
    Write-Output "================================================"
    
    Test-Environment
    Install-Uv
    Setup-PythonEnvironment
    
    if ($Clean) {
        Clear-Environment
    }
    
    Install-Dependencies
    
    if (-not $SkipTests) {
        Test-Setup
    }
    
    Show-EnvironmentInfo
    
    Log-Success "Windows environment setup completed!"
    Write-Output ""
    Log-Info "Next steps:"
    Write-Output "1. Run tests: uv run pytest"
    Write-Output "2. Start development server: uv run start-backend"
    Write-Output "3. Check available scripts: Select-String '\[project.scripts\]' -Path pyproject.toml -A 10"
    Write-Output ""
    Log-Info "Note: This was a Windows test. For actual Codex deployment, use scripts/setup_codex.sh"
}

# Run main function
Main 