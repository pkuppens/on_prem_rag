# Update Commits Command: Refresh All Repository Commits

## Purpose

This command updates all commit CSV files for the hours project by extracting the latest commits from all repositories listed in `repositories.csv`. It refreshes the commit data used for WBSO hours registration tracking.

## When to Use

- After making commits to any tracked repository
- When you need to refresh commit data for hours analysis
- Before generating WBSO reports that depend on commit data
- When repositories have been updated and you want the latest commit history

## Prerequisites

Before running this command, ensure:

- [ ] All repositories are cloned in the parent directory (default: `C:/Users/piete/Repos/pkuppens`)
- [ ] Git is installed and accessible
- [ ] Python environment is set up with required dependencies
- [ ] `repositories.csv` file exists at `docs/project/hours/data/repositories.csv`

## Command Execution Workflow

### Step 1: Verify Prerequisites

#### 1.1 Check Repositories File

**Windows PowerShell:**

```powershell
$REPOS_FILE = "docs/project/hours/data/repositories.csv"
if (-not (Test-Path $REPOS_FILE)) {
    Write-Host "❌ Repositories file not found: $REPOS_FILE" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Repositories file found: $REPOS_FILE" -ForegroundColor Green
```

**Unix/Linux/macOS:**

```bash
REPOS_FILE="docs/project/hours/data/repositories.csv"
if [ ! -f "$REPOS_FILE" ]; then
    echo "❌ Repositories file not found: $REPOS_FILE"
    exit 1
fi
echo "✅ Repositories file found: $REPOS_FILE"
```

#### 1.2 Check Commits Directory

**Windows PowerShell:**

```powershell
$COMMITS_DIR = "docs/project/hours/data/commits"
if (-not (Test-Path $COMMITS_DIR)) {
    New-Item -ItemType Directory -Force -Path $COMMITS_DIR | Out-Null
    Write-Host "✅ Created commits directory: $COMMITS_DIR" -ForegroundColor Green
} else {
    Write-Host "✅ Commits directory exists: $COMMITS_DIR" -ForegroundColor Green
}
```

**Unix/Linux/macOS:**

```bash
COMMITS_DIR="docs/project/hours/data/commits"
if [ ! -d "$COMMITS_DIR" ]; then
    mkdir -p "$COMMITS_DIR"
    echo "✅ Created commits directory: $COMMITS_DIR"
else
    echo "✅ Commits directory exists: $COMMITS_DIR"
fi
```

#### 1.3 Check Repository Parent Directory

**Windows PowerShell:**

```powershell
$REPO_PARENT_DIR = "C:/Users/piete/Repos/pkuppens"
if (-not (Test-Path $REPO_PARENT_DIR)) {
    Write-Host "❌ Repository parent directory not found: $REPO_PARENT_DIR" -ForegroundColor Red
    Write-Host "Please update the path in the command or clone repositories to this location." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Repository parent directory found: $REPO_PARENT_DIR" -ForegroundColor Green
```

**Unix/Linux/macOS:**

```bash
REPO_PARENT_DIR="$HOME/Repos/pkuppens"  # Adjust path as needed
if [ ! -d "$REPO_PARENT_DIR" ]; then
    echo "❌ Repository parent directory not found: $REPO_PARENT_DIR"
    echo "Please update the path in the command or clone repositories to this location."
    exit 1
fi
echo "✅ Repository parent directory found: $REPO_PARENT_DIR"
```

### Step 2: Run Update Script

#### 2.1 Execute Update Command

**Cross-platform (using uv):**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Run the update script
uv run python docs/project/hours/scripts/update_commits_from_repos.py
```

**With Custom Paths (if needed):**

```bash
uv run python docs/project/hours/scripts/update_commits_from_repos.py \
  --repos-file docs/project/hours/data/repositories.csv \
  --commits-dir docs/project/hours/data/commits \
  --repo-parent-dir "C:/Users/piete/Repos/pkuppens"
```

#### 2.2 Monitor Progress

The script will:

- Read repositories from `repositories.csv`
- Extract commits from each repository using git log
- Write commits to CSV files in `data/commits/` directory
- Provide progress logging and summary statistics

**Expected Output:**

```
INFO - Reading repositories from: docs/project/hours/data/repositories.csv
INFO - Output directory: docs/project/hours/data/commits
INFO - Repository parent directory: C:/Users/piete/Repos/pkuppens
INFO - Found 16 repositories to process
INFO - Processing repository: on_prem_rag
INFO - Extracting commits from on_prem_rag
INFO - Extracted 234 commits from on_prem_rag
INFO - Wrote 234 commits to docs/project/hours/data/commits/on_prem_rag.csv
...
INFO - ==================================================
INFO - EXTRACTION SUMMARY
INFO - ==================================================
INFO - Total repositories processed: 16
INFO - Errors encountered: 0
INFO - Output files created in: docs/project/hours/data/commits
```

### Step 3: Verify Results

#### 3.1 Check Output Files

**Windows PowerShell:**

```powershell
$COMMITS_DIR = "docs/project/hours/data/commits"
$CSV_FILES = Get-ChildItem -Path $COMMITS_DIR -Filter "*.csv"
Write-Host "✅ Found $($CSV_FILES.Count) commit CSV files:" -ForegroundColor Green
foreach ($file in $CSV_FILES) {
    $lineCount = (Get-Content $file.FullName | Measure-Object -Line).Lines - 1  # Subtract header
    Write-Host "  - $($file.Name): $lineCount commits" -ForegroundColor Cyan
}
```

**Unix/Linux/macOS:**

```bash
COMMITS_DIR="docs/project/hours/data/commits"
CSV_COUNT=$(find "$COMMITS_DIR" -name "*.csv" | wc -l)
echo "✅ Found $CSV_COUNT commit CSV files:"
for file in "$COMMITS_DIR"/*.csv; do
    if [ -f "$file" ]; then
        line_count=$(tail -n +2 "$file" | wc -l)  # Exclude header
        echo "  - $(basename "$file"): $line_count commits"
    fi
done
```

#### 3.2 Validate Commit Data Format

**Cross-platform:**

```bash
# Check a sample file to verify format
head -n 3 docs/project/hours/data/commits/on_prem_rag.csv
```

**Expected Format:**

```
datetime|timestamp|message|author|hash
2024-01-15 10:30:45|1705312245|Initial commit|Your Name|abc123def456...
2024-01-15 11:15:20|1705316120|Add feature X|Your Name|def456ghi789...
```

### Step 4: Handle Errors

#### 4.1 Repository Not Found

**Issue**: Repository directory doesn't exist

**Solution**:

- Verify repository is cloned in the parent directory
- Check repository name matches exactly (case-sensitive)
- Update `repositories.csv` if repository name is incorrect

#### 4.2 Git Command Timeout

**Issue**: Git command times out (5 minute limit)

**Solution**:

- Check if repository is corrupted or very large
- Try running git commands manually in the repository
- Consider excluding very large repositories from update

#### 4.3 No Commits Extracted

**Issue**: Repository exists but no commits are extracted

**Solution**:

- Verify repository has commits: `git log --oneline`
- Check if repository is a valid git repository: `git status`
- Verify git is accessible: `git --version`

#### 4.4 Permission Errors

**Issue**: Cannot write to commits directory

**Solution**:

- Check directory permissions
- Ensure you have write access to `docs/project/hours/data/commits`
- Create directory manually if needed

## Usage Examples

### Example 1: Standard Update

**Command:**

```bash
uv run python docs/project/hours/scripts/update_commits_from_repos.py
```

**Expected**: Updates all commit CSV files for all repositories in `repositories.csv`

### Example 2: Update with Custom Repository Path

**Command:**

```bash
uv run python docs/project/hours/scripts/update_commits_from_repos.py \
  --repo-parent-dir "/path/to/repositories"
```

**Expected**: Updates commits from repositories in the specified directory

### Example 3: Update Specific Repositories Only

**Edit `repositories.csv`** to include only the repositories you want to update, then run:

```bash
uv run python docs/project/hours/scripts/update_commits_from_repos.py
```

## Command Invocation

When user requests to update commits:

1. **Read this command file**: `.cursor/commands/update-commits.md`
2. **Verify prerequisites**: Check all required files and directories exist
3. **Execute update script**: Run `update_commits_from_repos.py` with appropriate parameters
4. **Monitor progress**: Watch for errors and warnings
5. **Verify results**: Check output files and validate data format
6. **Report summary**: Provide count of updated repositories and any errors

## Success Criteria

A successful commit update should result in:

- ✅ All repositories in `repositories.csv` processed
- ✅ Commit CSV files created/updated in `data/commits/` directory
- ✅ No critical errors (warnings for missing repos are acceptable)
- ✅ Commit data in correct format (datetime|timestamp|message|author|hash)
- ✅ Summary statistics showing processed repositories count

## Notes

- The script processes all repositories listed in `repositories.csv`
- Missing repositories are logged as warnings but don't stop the process
- Each repository's commits are written to a separate CSV file
- The script uses a 5-minute timeout per repository to prevent hanging
- Commit data is extracted using `git log` with reverse chronological order
- All commits from all branches are included (--all flag)

## Related Files

- **Script**: `docs/project/hours/scripts/update_commits_from_repos.py`
- **Repository List**: `docs/project/hours/data/repositories.csv`
- **Output Directory**: `docs/project/hours/data/commits/`
- **Documentation**: `docs/project/hours/README.md`
