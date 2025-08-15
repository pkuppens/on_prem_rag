# Repository Management Scripts

This directory contains scripts for managing repository access as part of the WBSO Hours Registration Retrofit Project.

## Scripts Overview

### 1. `clone_repositories.bat` (Windows Batch)

- **Purpose**: Clone or update all repositories listed in `data/repositories.csv`
- **Usage**: Double-click the file or run from command prompt
- **Features**:
  - Reads CSV file with repository information
  - Checks if repositories already exist
  - Updates existing repositories with `git pull`
  - Clones new repositories with `git clone`
  - Logs all operations to `data/clone_log.txt`

### 2. `clone_repositories.ps1` (PowerShell)

- **Purpose**: Same functionality as batch file but with better CSV parsing
- **Usage**: Run from PowerShell with execution policy that allows scripts
- **Features**:
  - Better CSV parsing using PowerShell's `Import-Csv`
  - More detailed logging with timestamps
  - Summary report generation
  - Better error handling

## Prerequisites

1. **Git**: Ensure Git is installed and accessible from command line
2. **Repository Access**: Ensure you have access to all repositories in the CSV file
3. **Directory Structure**: The script expects the following structure:
   ```
   docs/project/hours/
   ├── scripts/
   │   ├── clone_repositories.bat
   │   ├── clone_repositories.ps1
   │   └── README.md
   └── data/
       └── repositories.csv
   ```

## Usage Instructions

### Option 1: Windows Batch Script

1. Navigate to the scripts directory
2. Double-click `clone_repositories.bat` or run from command prompt:
   ```cmd
   cd docs\project\hours\scripts
   clone_repositories.bat
   ```

### Option 2: PowerShell Script

1. Open PowerShell
2. Navigate to the scripts directory
3. Run the script:
   ```powershell
   cd docs\project\hours\scripts
   .\clone_repositories.ps1
   ```

## Configuration

The scripts are configured to:

- **Repository Parent Directory**: `C:\Users\piete\Repos\pkuppens`
- **CSV File**: `../data/repositories.csv`
- **Log File**: `../data/clone_log.txt`

You can modify these paths in the script files if needed.

## Expected Output

After running the script, you should have:

1. All repositories cloned/updated in `C:\Users\piete\Repos\pkuppens`
2. A log file at `docs/project/hours/data/clone_log.txt` with operation details
3. Console output showing progress for each repository

## Troubleshooting

### Common Issues

1. **Git not found**: Ensure Git is installed and in your PATH
2. **Access denied**: Check that you have access to the repositories
3. **CSV file not found**: Verify the path to `repositories.csv` is correct
4. **Network issues**: Check your internet connection for cloning operations

### Log File Analysis

The log file contains detailed information about each operation:

- Repository names being processed
- Success/failure status for each operation
- Error messages for failed operations
- Summary statistics

## Next Steps

After successfully running the repository management script:

1. Verify all repositories are accessible
2. Proceed to Step 1.2: Git Commit Data Extraction
3. Check the log file for any issues that need resolution
