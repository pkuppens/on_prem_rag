# Commit Command: Create Good Commits with Quality Checks

## Purpose

This command creates well-structured commit messages following project standards, with automatic linting and formatting fixes, support for quality checks, partial commits, and automatic tag inference from branch names and changes.

**Key Features:**
- **Automatic linting**: Always runs `ruff check --fix` and `ruff format` before committing to prevent CI/CD failures
- **Auto-fix integration**: Automatically fixes linting issues and re-stages modified files
- **Quality checks**: Optional test execution with "require tests" hint
- **Smart commit messages**: Infers tags from branch names and change types
- **Partial commits**: Support for creating focused, smaller commits

## When to Use

- After making code changes and ready to commit
- When you want to ensure commit quality before pushing
- When you need to create partial commits for smaller pieces of work
- When you want automatic tag inference from branch names
- When you need to run tests before committing

## Prerequisites

Before running this command, ensure:

- [ ] Git is installed and accessible
- [ ] You are in a git repository
- [ ] You have changes staged or ready to stage
- [ ] Python environment is set up (if running tests)
- [ ] You understand what changes you want to commit

## Command Execution Workflow

### Step 1: Analyze Current Context

#### 1.1 Get Current Branch

**Cross-platform:**

```bash
# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
```

**Windows PowerShell:**

```powershell
$CURRENT_BRANCH = git branch --show-current
Write-Host "Current branch: $CURRENT_BRANCH"
```

#### 1.2 Extract Tags from Branch Name

**Cross-platform:**

```bash
# Extract TASK-XXX, STORY-XXX, FEAT-XXX from branch name
TASK_ID=$(echo "$CURRENT_BRANCH" | grep -oE 'TASK-\d+' || echo "")
STORY_ID=$(echo "$CURRENT_BRANCH" | grep -oE 'STORY-\d+' || echo "")
FEAT_ID=$(echo "$CURRENT_BRANCH" | grep -oE 'FEAT-\d+' || echo "")
BUG_ID=$(echo "$CURRENT_BRANCH" | grep -oE 'BUG-\d+' || echo "")
HOTFIX_ID=$(echo "$CURRENT_BRANCH" | grep -oE 'HOTFIX-\d+' || echo "")

# Determine branch type
if [[ "$CURRENT_BRANCH" == feature/* ]]; then
    BRANCH_TYPE="feature"
elif [[ "$CURRENT_BRANCH" == task/* ]]; then
    BRANCH_TYPE="task"
elif [[ "$CURRENT_BRANCH" == bug/* ]]; then
    BRANCH_TYPE="bugfix"
elif [[ "$CURRENT_BRANCH" == hotfix/* ]]; then
    BRANCH_TYPE="hotfix"
else
    BRANCH_TYPE="other"
fi
```

**Windows PowerShell:**

```powershell
# Extract TASK-XXX, STORY-XXX, FEAT-XXX from branch name
$TASK_ID = if ($CURRENT_BRANCH -match 'TASK-\d+') { $matches[0] } else { "" }
$STORY_ID = if ($CURRENT_BRANCH -match 'STORY-\d+') { $matches[0] } else { "" }
$FEAT_ID = if ($CURRENT_BRANCH -match 'FEAT-\d+') { $matches[0] } else { "" }
$BUG_ID = if ($CURRENT_BRANCH -match 'BUG-\d+') { $matches[0] } else { "" }
$HOTFIX_ID = if ($CURRENT_BRANCH -match 'HOTFIX-\d+') { $matches[0] } else { "" }

# Determine branch type
if ($CURRENT_BRANCH -like "feature/*") {
    $BRANCH_TYPE = "feature"
} elseif ($CURRENT_BRANCH -like "task/*") {
    $BRANCH_TYPE = "task"
} elseif ($CURRENT_BRANCH -like "bug/*") {
    $BRANCH_TYPE = "bugfix"
} elseif ($CURRENT_BRANCH -like "hotfix/*") {
    $BRANCH_TYPE = "hotfix"
} else {
    $BRANCH_TYPE = "other"
}
```

#### 1.3 Analyze Staged Changes

**Cross-platform:**

```bash
# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

# Count changes by type
NEW_FILES=$(git diff --cached --name-only --diff-filter=A | wc -l)
MODIFIED_FILES=$(git diff --cached --name-only --diff-filter=M | wc -l)
DELETED_FILES=$(git diff --cached --name-only --diff-filter=D | wc -l)

# Determine change scope
if echo "$STAGED_FILES" | grep -q "^src/"; then
    SCOPE="code"
elif echo "$STAGED_FILES" | grep -q "^tests/"; then
    SCOPE="test"
elif echo "$STAGED_FILES" | grep -q "^docs/"; then
    SCOPE="docs"
elif echo "$STAGED_FILES" | grep -q "^\.cursor/"; then
    SCOPE="config"
else
    SCOPE="other"
fi

# Determine commit type based on changes
if echo "$STAGED_FILES" | grep -qE "\.(py|ts|tsx|js|jsx)$"; then
    if echo "$STAGED_FILES" | grep -q "^tests/"; then
        COMMIT_TYPE="test"
    elif echo "$STAGED_FILES" | grep -qE "(fix|bug|error|issue)"; then
        COMMIT_TYPE="fix"
    else
        COMMIT_TYPE="feat"
    fi
elif echo "$STAGED_FILES" | grep -qE "\.(md|mdx)$"; then
    COMMIT_TYPE="docs"
elif echo "$STAGED_FILES" | grep -qE "(\.toml|\.json|\.yml|\.yaml)$"; then
    COMMIT_TYPE="chore"
else
    COMMIT_TYPE="chore"
fi
```

**Windows PowerShell:**

```powershell
# Get list of staged files
$STAGED_FILES = git diff --cached --name-only

# Count changes by type
$NEW_FILES = (git diff --cached --name-only --diff-filter=A | Measure-Object).Count
$MODIFIED_FILES = (git diff --cached --name-only --diff-filter=M | Measure-Object).Count
$DELETED_FILES = (git diff --cached --name-only --diff-filter=D | Measure-Object).Count

# Determine change scope
if ($STAGED_FILES -match "^src/") {
    $SCOPE = "code"
} elseif ($STAGED_FILES -match "^tests/") {
    $SCOPE = "test"
} elseif ($STAGED_FILES -match "^docs/") {
    $SCOPE = "docs"
} elseif ($STAGED_FILES -match "^\.cursor/") {
    $SCOPE = "config"
} else {
    $SCOPE = "other"
}

# Determine commit type based on changes
if ($STAGED_FILES -match "\.(py|ts|tsx|js|jsx)$") {
    if ($STAGED_FILES -match "^tests/") {
        $COMMIT_TYPE = "test"
    } elseif ($STAGED_FILES -match "(fix|bug|error|issue)") {
        $COMMIT_TYPE = "fix"
    } else {
        $COMMIT_TYPE = "feat"
    }
} elseif ($STAGED_FILES -match "\.(md|mdx)$") {
    $COMMIT_TYPE = "docs"
} elseif ($STAGED_FILES -match "(\.toml|\.json|\.yml|\.yaml)$") {
    $COMMIT_TYPE = "chore"
} else {
    $COMMIT_TYPE = "chore"
}
```

### Step 2: Automatic Linting and Formatting

**CRITICAL**: This step always runs before committing to ensure code quality and prevent GitHub Actions failures.

#### 2.1 Run Automatic Linting Fixes

**Check for "skip linting" hint:**

Before running linting, check if user requested to skip it (not recommended):

**Cross-platform:**

```bash
# Check for skip linting hint
SKIP_LINTING=false
if [[ "$*" =~ (skip[[:space:]]+linting|skip[[:space:]]+lint) ]]; then
    SKIP_LINTING=true
    echo "⚠️  Skipping automatic linting (not recommended - may cause CI failures)"
fi

if [ "$SKIP_LINTING" = false ]; then
    # Run ruff check with --fix to automatically fix linting issues
    echo "Running ruff check --fix..."
    uv run ruff check --fix . || {
        echo "❌ Linting failed. Some issues could not be auto-fixed."
        echo "Please review and fix remaining issues before committing."
        exit 1
    }

    # Run ruff format to automatically format code
    echo "Running ruff format..."
    uv run ruff format . || {
        echo "❌ Formatting failed."
        exit 1
    }

    echo "✅ Linting and formatting complete!"
    
    # Re-stage any files that were auto-fixed
    echo "Re-staging auto-fixed files..."
    git add -u
fi
```

**Windows PowerShell:**

```powershell
# Check for skip linting hint
$SKIP_LINTING = $false
if ($args -match "(skip\s+linting|skip\s+lint)") {
    $SKIP_LINTING = $true
    Write-Host "⚠️  Skipping automatic linting (not recommended - may cause CI failures)" -ForegroundColor Yellow
}

if (-not $SKIP_LINTING) {
    # Run ruff check with --fix to automatically fix linting issues
    Write-Host "Running ruff check --fix..." -ForegroundColor Cyan
    uv run ruff check --fix .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Linting failed. Some issues could not be auto-fixed." -ForegroundColor Red
        Write-Host "Please review and fix remaining issues before committing." -ForegroundColor Yellow
        exit 1
    }

    # Run ruff format to automatically format code
    Write-Host "Running ruff format..." -ForegroundColor Cyan
    uv run ruff format .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Formatting failed." -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Linting and formatting complete!" -ForegroundColor Green
    
    # Re-stage any files that were auto-fixed
    Write-Host "Re-staging auto-fixed files..." -ForegroundColor Cyan
    git add -u
}
```

### Step 3: Handle Hints and Options

#### 3.1 Parse User Hints

The command accepts hints in the user's request:

- **"require tests"** or **"run tests"**: Run tests before committing
- **"partial commit"** or **"small commit"**: Create a smaller, focused commit
- **"skip tests"**: Skip test execution (not recommended)
- **"skip linting"**: Skip automatic linting (not recommended, may cause CI failures)
- **"description: [text]"**: Add custom description to commit message
- **"type: [feat|fix|docs|test|chore]"**: Override commit type
- **"scope: [scope]"**: Override commit scope

#### 3.2 Quality Checks (if "require tests" hint)

**Cross-platform:**

```bash
# Run linting check
echo "Running linting check..."
uv run ruff check . || {
    echo "❌ Linting failed. Fix issues before committing."
    exit 1
}

# Run formatting check
echo "Running formatting check..."
uv run ruff format --check . || {
    echo "⚠️  Formatting issues found. Run 'uv run ruff format .' to fix."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Run tests (fast unit tests only)
echo "Running tests..."
uv run pytest -m "not internet and not slow" -v || {
    echo "❌ Tests failed. Fix issues before committing."
    exit 1
}

echo "✅ All quality checks passed!"
```

**Windows PowerShell:**

```powershell
# Run linting check
Write-Host "Running linting check..."
uv run ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Linting failed. Fix issues before committing." -ForegroundColor Red
    exit 1
}

# Run formatting check
Write-Host "Running formatting check..."
uv run ruff format --check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Formatting issues found. Run 'uv run ruff format .' to fix." -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Run tests (fast unit tests only)
Write-Host "Running tests..."
uv run pytest -m "not internet and not slow" -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed. Fix issues before committing." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All quality checks passed!" -ForegroundColor Green
```

### Step 4: Generate Commit Message

#### 4.1 Build Commit Message

**Cross-platform:**

```bash
# Create tmp directory if it doesn't exist
mkdir -p tmp

# Start building commit message
COMMIT_MSG_FILE="tmp/commit_msg.txt"

# Build header
if [ -n "$TASK_ID" ]; then
    HEADER="${COMMIT_TYPE}(${SCOPE}): ${TASK_ID}: "
elif [ -n "$STORY_ID" ]; then
    HEADER="${COMMIT_TYPE}(${SCOPE}): ${STORY_ID}: "
elif [ -n "$FEAT_ID" ]; then
    HEADER="${COMMIT_TYPE}(${SCOPE}): ${FEAT_ID}: "
elif [ -n "$BUG_ID" ]; then
    HEADER="${COMMIT_TYPE}(${SCOPE}): ${BUG_ID}: "
elif [ -n "$HOTFIX_ID" ]; then
    HEADER="${COMMIT_TYPE}(${SCOPE}): ${HOTFIX_ID}: "
else
    HEADER="${COMMIT_TYPE}(${SCOPE}): "
fi

# Generate description from changes
DESCRIPTION=$(git diff --cached --stat | head -1 | sed 's/^[^|]*| //' | sed 's/ |.*$//' | tr -d '\n')

# If custom description provided, use it
if [ -n "$CUSTOM_DESCRIPTION" ]; then
    DESCRIPTION="$CUSTOM_DESCRIPTION"
fi

# Write commit message
cat > "$COMMIT_MSG_FILE" << EOF
${HEADER}${DESCRIPTION}

EOF

# Add change summary
echo "- Changes:" >> "$COMMIT_MSG_FILE"
git diff --cached --name-status | while read status file; do
    case "$status" in
        A*) echo "  - Added: $file" >> "$COMMIT_MSG_FILE" ;;
        M*) echo "  - Modified: $file" >> "$COMMIT_MSG_FILE" ;;
        D*) echo "  - Deleted: $file" >> "$COMMIT_MSG_FILE" ;;
        R*) echo "  - Renamed: $file" >> "$COMMIT_MSG_FILE" ;;
    esac
done

# Add references
echo "" >> "$COMMIT_MSG_FILE"
echo "Refs:" >> "$COMMIT_MSG_FILE"
[ -n "$TASK_ID" ] && echo "  - $TASK_ID" >> "$COMMIT_MSG_FILE"
[ -n "$STORY_ID" ] && echo "  - $STORY_ID" >> "$COMMIT_MSG_FILE"
[ -n "$FEAT_ID" ] && echo "  - $FEAT_ID" >> "$COMMIT_MSG_FILE"
[ -n "$BUG_ID" ] && echo "  - $BUG_ID" >> "$COMMIT_MSG_FILE"
[ -n "$HOTFIX_ID" ] && echo "  - $HOTFIX_ID" >> "$COMMIT_MSG_FILE"
```

**Windows PowerShell:**

```powershell
# Create tmp directory if it doesn't exist
if (-not (Test-Path "tmp")) {
    New-Item -ItemType Directory -Path "tmp" | Out-Null
}

# Start building commit message
$COMMIT_MSG_FILE = "tmp/commit_msg.txt"

# Build header
$HEADER = ""
if ($TASK_ID) {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): ${TASK_ID}: "
} elseif ($STORY_ID) {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): ${STORY_ID}: "
} elseif ($FEAT_ID) {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): ${FEAT_ID}: "
} elseif ($BUG_ID) {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): ${BUG_ID}: "
} elseif ($HOTFIX_ID) {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): ${HOTFIX_ID}: "
} else {
    $HEADER = "${COMMIT_TYPE}(${SCOPE}): "
}

# Generate description from changes
$DESCRIPTION = (git diff --cached --stat | Select-Object -First 1) -replace '^[^|]*\| ', '' -replace ' \|.*$', ''

# If custom description provided, use it
if ($CUSTOM_DESCRIPTION) {
    $DESCRIPTION = $CUSTOM_DESCRIPTION
}

# Write commit message
@"
${HEADER}${DESCRIPTION}

"@ | Out-File -FilePath $COMMIT_MSG_FILE -Encoding utf8

# Add change summary
Add-Content -Path $COMMIT_MSG_FILE -Value "- Changes:"
git diff --cached --name-status | ForEach-Object {
    $line = $_
    if ($line -match '^A\s+(.+)') {
        Add-Content -Path $COMMIT_MSG_FILE -Value "  - Added: $($matches[1])"
    } elseif ($line -match '^M\s+(.+)') {
        Add-Content -Path $COMMIT_MSG_FILE -Value "  - Modified: $($matches[1])"
    } elseif ($line -match '^D\s+(.+)') {
        Add-Content -Path $COMMIT_MSG_FILE -Value "  - Deleted: $($matches[1])"
    } elseif ($line -match '^R\s+(.+)') {
        Add-Content -Path $COMMIT_MSG_FILE -Value "  - Renamed: $($matches[1])"
    }
}

# Add references
Add-Content -Path $COMMIT_MSG_FILE -Value ""
Add-Content -Path $COMMIT_MSG_FILE -Value "Refs:"
if ($TASK_ID) { Add-Content -Path $COMMIT_MSG_FILE -Value "  - $TASK_ID" }
if ($STORY_ID) { Add-Content -Path $COMMIT_MSG_FILE -Value "  - $STORY_ID" }
if ($FEAT_ID) { Add-Content -Path $COMMIT_MSG_FILE -Value "  - $FEAT_ID" }
if ($BUG_ID) { Add-Content -Path $COMMIT_MSG_FILE -Value "  - $BUG_ID" }
if ($HOTFIX_ID) { Add-Content -Path $COMMIT_MSG_FILE -Value "  - $HOTFIX_ID" }
```

#### 4.2 Review Commit Message

**Cross-platform:**

```bash
# Display commit message for review
echo "=========================================="
echo "Generated Commit Message:"
echo "=========================================="
cat "$COMMIT_MSG_FILE"
echo "=========================================="
echo ""
echo "Review the commit message above."
echo "File saved to: $COMMIT_MSG_FILE"
echo ""
read -p "Proceed with commit? (Y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo "Commit cancelled. Edit $COMMIT_MSG_FILE and commit manually."
    exit 0
fi
```

**Windows PowerShell:**

```powershell
# Display commit message for review
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Generated Commit Message:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Get-Content $COMMIT_MSG_FILE
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Review the commit message above." -ForegroundColor Yellow
Write-Host "File saved to: $COMMIT_MSG_FILE" -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "Proceed with commit? (Y/n)"
if ($response -eq "n" -or $response -eq "N") {
    Write-Host "Commit cancelled. Edit $COMMIT_MSG_FILE and commit manually." -ForegroundColor Yellow
    exit 0
}
```

### Step 5: Handle Partial Commits

#### 5.1 Interactive Staging (if "partial commit" hint)

**Cross-platform:**

```bash
# Show unstaged changes
echo "Unstaged changes:"
git status --short

# Prompt for file selection
echo ""
echo "Select files to include in this commit (space-separated):"
read -p "Files: " FILES_TO_STAGE

# Stage selected files
for file in $FILES_TO_STAGE; do
    git add "$file"
done

# Regenerate commit message with new staged files
# (Repeat Step 3.1)
```

**Windows PowerShell:**

```powershell
# Show unstaged changes
Write-Host "Unstaged changes:"
git status --short

# Prompt for file selection
Write-Host ""
$FILES_TO_STAGE = Read-Host "Select files to include in this commit (space-separated)"

# Stage selected files
$FILES_TO_STAGE -split ' ' | ForEach-Object {
    git add $_
}

# Regenerate commit message with new staged files
# (Repeat Step 3.1)
```

### Step 6: Execute Commit

#### 6.1 Commit with Generated Message

**Cross-platform:**

```bash
# Commit using the message file
git commit -F "$COMMIT_MSG_FILE"

# Show commit summary
echo ""
echo "✅ Commit created successfully!"
echo ""
git log -1 --stat
```

**Windows PowerShell:**

```powershell
# Commit using the message file
git commit -F $COMMIT_MSG_FILE

# Show commit summary
Write-Host ""
Write-Host "✅ Commit created successfully!" -ForegroundColor Green
Write-Host ""
git log -1 --stat
```

## Usage Examples

### Example 1: Standard Commit with Auto-Detection

**Command:**

```bash
# User says: "Create a commit"
# Or: "Commit these changes"
```

**Expected Behavior:**

- Analyzes current branch for tags
- Analyzes staged changes for type and scope
- **Runs automatic linting and formatting** (`ruff check --fix` and `ruff format`)
- Re-stages any auto-fixed files
- Generates commit message following project standards
- Creates `tmp/commit_msg.txt` with commit message
- Commits using the generated message

### Example 2: Commit with Tests Required

**Command:**

```bash
# User says: "Create a commit, require tests"
# Or: "Commit with tests"
```

**Expected Behavior:**

- Runs automatic linting and formatting (always runs)
- Runs tests (fast unit tests only)
- Only proceeds if all checks pass
- Generates and commits with message

**Note**: Linting and formatting run automatically even without this hint. This hint only adds test execution.

### Example 3: Partial Commit

**Command:**

```bash
# User says: "Create a partial commit"
# Or: "Commit only the test files"
```

**Expected Behavior:**

- Shows unstaged changes
- Prompts for file selection
- Stages only selected files
- Generates commit message for selected files
- Commits smaller, focused changeset

### Example 4: Commit with Custom Description

**Command:**

```bash
# User says: "Create a commit, description: Fix memory leak in PDF processing"
```

**Expected Behavior:**

- Uses custom description instead of auto-generated one
- Still infers tags from branch name
- Still analyzes changes for type and scope
- Includes custom description in commit message

### Example 5: Commit with Type Override

**Command:**

```bash
# User says: "Create a commit, type: fix"
```

**Expected Behavior:**

- Overrides auto-detected commit type
- Uses "fix" instead of detected type
- Still infers tags and scope from context

## Command Invocation

When user requests to create a commit:

1. **Read this command file**: `.cursor/commands/commit.md`
2. **Analyze context**: Extract branch name, tags, and staged changes
3. **Run automatic linting**: Always run `ruff check --fix` and `ruff format` to fix issues automatically
4. **Re-stage auto-fixed files**: Stage any files modified by ruff auto-fix
5. **Parse hints**: Check for "require tests", "partial commit", custom description, etc.
6. **Run quality checks**: If "require tests" hint, run tests
7. **Generate commit message**: Create well-structured message following project standards
8. **Handle partial commits**: If requested, allow interactive file selection
9. **Review message**: Display generated message for user review
10. **Execute commit**: Commit using the generated message file
11. **Report success**: Show commit summary

## Success Criteria

A successful commit should result in:

- ✅ Commit message follows conventional commit format
- ✅ Tags (TASK-XXX, STORY-XXX, FEAT-XXX) inferred from branch name
- ✅ Commit type and scope determined from changes
- ✅ Commit message saved to `tmp/commit_msg.txt`
- ✅ Commit message only references committed files
- ✅ Quality checks pass (if "require tests" hint)
- ✅ Commit created successfully with proper message

## Commit Message Format

The generated commit message follows this structure:

```
<type>(<scope>): <TASK/STORY/FEAT-ID>: <description>

- Changes:
  - Added: <file>
  - Modified: <file>
  - Deleted: <file>

Refs:
  - TASK-XXX
  - STORY-XXX
  - FEAT-XXX
```

**Example:**

```
feat(rag): TASK-005: implement document chunking with overlap

- Changes:
  - Added: src/rag_pipeline/core/chunking.py
  - Modified: tests/test_chunking.py
  - Modified: docs/technical/CHUNKING.md

Refs:
  - TASK-005
  - STORY-002
```

## Quality Checks

### Automatic Linting and Formatting (Always Runs)

**CRITICAL**: These checks run automatically before every commit to prevent GitHub Actions failures.

- **Linting**: Runs `uv run ruff check --fix .`
  - Automatically fixes all fixable linting issues
  - Fails if non-fixable issues remain (must be fixed manually)
  - Prevents linting errors in CI/CD pipelines
  
- **Formatting**: Runs `uv run ruff format .`
  - Automatically formats all code files
  - Ensures consistent code style
  - Prevents formatting errors in CI/CD pipelines

- **Auto-fixed files**: After running ruff, modified files are automatically re-staged with `git add -u`

### Test Execution (Optional - Requires "require tests" hint)

- Runs `uv run pytest -m "not internet and not slow" -v`
- Only runs fast unit tests (excludes slow and internet-dependent tests)
- Fails if any tests fail
- Must be fixed before committing
- Can be skipped with "skip tests" hint (not recommended)

## Partial Commits

Partial commits allow you to:

- **Split large changesets**: Commit related changes separately
- **Focus on specific files**: Commit only files that belong together
- **Maintain clean history**: Keep commits small and focused
- **Follow single responsibility**: Each commit addresses one concern

**When to use:**

- Large refactoring split into logical pieces
- Multiple features implemented together
- Documentation updates separate from code changes
- Test updates separate from implementation

## Tag Inference

Tags are automatically inferred from:

1. **Branch name**: Extracts TASK-XXX, STORY-XXX, FEAT-XXX, BUG-XXX, HOTFIX-XXX
2. **Branch type**: Determines if feature, task, bugfix, or hotfix
3. **Change analysis**: Determines commit type (feat, fix, docs, test, chore)
4. **File paths**: Determines scope (code, test, docs, config, other)

**Branch naming patterns:**

- `feature/FEAT-003-wbso-calendar-completion` → FEAT-003
- `task/TASK-030-pandas-integration` → TASK-030
- `bug/BUG-012-memory-leak` → BUG-012
- `hotfix/HOTFIX-001-security-patch` → HOTFIX-001

## Notes

- **Automatic linting and formatting always runs** before committing to prevent CI/CD failures
- Commit messages are saved to `tmp/commit_msg.txt` for review and reuse
- The command follows [commit-message-standards.mdc](mdc:.cursor/rules/commit-message-standards.mdc)
- Commit messages only reference committed files (not tmp/ directory)
- Auto-fixed files are automatically re-staged after ruff runs
- Test execution is optional (requires "require tests" hint)
- Partial commits help maintain clean git history
- Tag inference works best with proper branch naming conventions
- Use "skip linting" hint only in emergency situations (may cause CI failures)

## Related Files

- **Rule**: `.cursor/rules/commit-message-standards.mdc` - Commit message standards
- **Rule**: `.cursor/rules/git-version-control.mdc` - Git version control standards
- **Rule**: `.cursor/rules/github-integration.mdc` - Branch naming conventions
- **Command**: `.cursor/commands/pr.md` - Pull request creation workflow

---

End Command ---
