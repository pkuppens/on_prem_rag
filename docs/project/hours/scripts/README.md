# Hours Registration Scripts

This directory contains scripts for automating the extraction and processing of work hours data from Git repositories.

## Scripts Overview

### Shared Configuration

- `config.bat` - Shared configuration file with paths and settings
- `utils.bat` - Shared utility functions for common operations

### Repository Management

- `clone_repositories.bat` - Windows batch script to clone repositories
- `clone_repositories.ps1` - PowerShell script to clone repositories

### Git Commit Data Extraction

- `extract_git_commits.bat` - Windows batch script to extract Git commit data
- `extract_git_commits.ps1` - PowerShell script to extract Git commit data

## Shared Configuration

### Purpose

The scripts use shared configuration and utilities to ensure consistency and maintainability.

### Configuration Files

- **`config.bat`**: Contains all paths, settings, and Git options

  - Repository parent directory: `C:\Users\piete\Repos\pkuppens\`
  - CSV file location: `../data/repositories.csv`
  - Output directories and log files
  - Git log format and options

- **`utils.bat`**: Contains common functions used by multiple scripts
  - Log file initialization and message logging
  - Directory creation and existence checks
  - Repository path handling
  - CSV file validation

### Benefits

- **Consistency**: All scripts use the same paths and settings
- **Maintainability**: Changes to paths only need to be made in one place
- **Reusability**: Common functions are shared between scripts
- **Error Handling**: Standardized error checking and logging

## Git Commit Data Extraction

### Purpose

Extract commit history from all repositories listed in `../data/repositories.csv` to support WBSO hours registration.

### Prerequisites

1. All repositories must be cloned to `C:\Users\piete\Repos\pkuppens\` (configured in `config.bat`)
2. Git must be installed and accessible from command line
3. `../data/repositories.csv` must exist with repository information

### Usage

#### Windows Batch Script

```cmd
cd docs/project/hours/scripts
extract_git_commits.bat
```

#### PowerShell Script

```powershell
cd docs/project/hours/scripts
.\extract_git_commits.ps1
```

### Output

- **Commit files**: `../data/commits/{repo_name}.csv` for each repository
- **Log file**: `../data/git_extraction_log.txt` with detailed execution log
- **Format**: Each CSV contains commit data with columns: datetime, timestamp, message, author, hash

### Git Log Format

The scripts use the following Git log format:

```
git log --pretty=format:"%ad|%at|%s|%an|%H" --date=iso --reverse --all
```

This produces output with:

- `%ad` - Author date (ISO format)
- `%at` - Author date (Unix timestamp)
- `%s` - Subject (commit message)
- `%an` - Author name
- `%H` - Commit hash

**Note**: The batch script uses `%%ad|%%at|%%s|%%an|%%H` format (double percent signs) to properly escape the format string in batch files.

### Error Handling

- Scripts log all operations to `git_extraction_log.txt`
- Missing repositories are reported but don't stop processing
- Git errors are captured and logged
- Summary statistics are provided at the end

### Validation

After running the script, verify:

1. CSV files exist in `../data/commits/` for each repository
2. Each CSV contains commit data with proper formatting
3. Check `git_extraction_log.txt` for any errors or warnings

### Testing Git Log Format

To test the git log format manually:

```cmd
# Test batch script format
git --no-pager log --pretty=format:"%%ad|%%at|%%s|%%an|%%H" --date=iso --reverse --all -n 3

# Test PowerShell format
git --no-pager log --pretty=format:"%ad|%at|%s|%an|%H" --date=iso --reverse --all -n 3
```

Or use the test script:

```cmd
cd docs/project/hours/scripts
test_git_format.bat
```

## Repository Cloning

### Purpose

Clone all repositories listed in `../data/repositories.csv` for local processing.

### Usage

#### Windows Batch Script

```cmd
cd docs/project/hours/scripts
clone_repositories.bat
```

#### PowerShell Script

```powershell
cd docs/project/hours/scripts
.\clone_repositories.ps1
```

### Output

- **Repositories**: Cloned to `C:\Users\piete\Repos\pkuppens\` (configured in `config.bat`)
- **Log file**: `../data/clone_log.txt` with cloning results

## File Structure

```
docs/project/hours/
├── scripts/
│   ├── config.bat              # Shared configuration
│   ├── utils.bat               # Shared utilities
│   ├── clone_repositories.bat
│   ├── clone_repositories.ps1
│   ├── extract_git_commits.bat
│   ├── extract_git_commits.ps1
│   └── README.md
├── data/
│   ├── repositories.csv
│   ├── commits/
│   │   └── {repo_name}.csv
│   ├── clone_log.txt
│   └── git_extraction_log.txt
└── PROJECT_PLAN.md
```

## Troubleshooting

### Common Issues

1. **Repository not found**: Ensure repositories are cloned before running extraction
2. **Git not found**: Verify Git is installed and in PATH
3. **Permission errors**: Run scripts with appropriate permissions
4. **CSV parsing errors**: Check repository names for special characters
5. **Git log format issues**:
   - Batch script uses `%%ad|%%at|%%s|%%an|%%H` (double percent signs for escaping)
   - PowerShell script uses `%ad|%at|%s|%an|%H` (single percent signs)
   - Use `--no-pager` flag to prevent paging issues
6. **Empty output files**: Check if repositories have commits and git log permissions

### Log Files

- Check `../data/git_extraction_log.txt` for detailed error information
- Check `../data/clone_log.txt` for cloning issues
- Both scripts provide summary statistics at completion
