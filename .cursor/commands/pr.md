# PR Command: Create Pull Request

## Purpose

This command provides a comprehensive, step-by-step process for creating pull requests that are **first-time-right** and will pass GitHub Actions. It validates code quality, checks acceptance criteria, generates AI-enhanced descriptions, and creates PRs following all project standards.

## Redirect To (do not duplicate)

- **Issue workflow**: Use `/get-started` when starting from an issue (Validate → Plan → Implement).
- **Commits**: Use `/commit` before this command; all changes must be committed first.
- **Pre-flight checks**: Same quality gates as `/commit` (ruff, format, pytest). Do not re-implement; reference [commit.md](.cursor/commands/commit.md) Quality Checks section.
- **tmp/ for PR body**: Use `tmp/github/pr-descriptions/` per [temp-files.mdc](.cursor/rules/temp-files.mdc).

## When to Use

- After completing a task or story implementation
- When ready to merge feature/task/hotfix branches
- Before any code review or merge process
- When you want to ensure PR will pass all quality gates

## Prerequisites

Before running this command, ensure:

- [ ] You are on the correct branch (feature/TASK-XXX, story/STORY-XXX, etc.)
- [ ] All code changes are committed
- [ ] GitHub CLI is installed and authenticated (`gh auth status`)
- [ ] You have push access to the repository

## Lessons Learned

### Task File Location Discovery

**Issue**: Task files may not match the exact branch name format.

**Solution**: Task files are located at `project/team/tasks/TASK-XXX.md` where XXX is just the number (e.g., `TASK-030.md`), not the full branch description. When extracting from branch names like `feature/TASK-030-pandas-integration`:

- Extract the TASK-XXX pattern (e.g., `TASK-030`)
- Look for file at `project/team/tasks/TASK-030.md` (not `TASK-030-pandas-integration.md`)
- Use glob search as fallback: `**/TASK-030*.md`

**Example**:

```bash
# Branch: feature/TASK-030-pandas-integration
# Task file: project/team/tasks/TASK-030.md (NOT TASK-030-pandas-integration.md)
```

### Story File Location

Story files follow the same pattern at `project/team/stories/STORY-XXX.md`.

### Base Branch for PR (branch-off-non-main)

**Default**: PR targets `main`; use `origin/main` for diff and log.

**When branch was created from non-main** (see [branch-policy.mdc](.cursor/rules/branch-policy.mdc)): Check `tmp/github/progress/issue-NNN-workflow.md` for `base_branch: <branch>`. If present, use that branch for `git diff origin/<branch>...HEAD`, `git log origin/<branch>...HEAD`, and `gh pr create --base <branch>`.

## Command Execution Workflow

### Step 1: Pre-Flight Validation

**CRITICAL**: If any validation fails, **DO NOT** create the PR. Instead, report the issues with a checkbox list.

#### 1.1 Linting Check

```bash
uv run ruff check .
```

**Expected**: "All checks passed!"
**If fails**: List specific linting errors and provide fix instructions

#### 1.2 Formatting Check

```bash
uv run ruff format --check .
```

**Expected**: "X files already formatted"
**If fails**: Run `uv run ruff format .` and commit changes

#### 1.3 Test Suite Validation

```bash
uv run pytest -m "not internet and not slow" -v
```

**Expected**: All tests pass (matches GitHub Actions configuration)
**If fails**: List failed tests and provide debugging guidance

#### 1.4 Git Status Check

```bash
git status
```

**Expected**: "nothing to commit, working tree clean"
**If fails**: List uncommitted files and prompt to commit or stash

**CRITICAL**: A PR should represent complete development work. All changes must be committed before creating the PR.

#### 1.5 Branch and Task Validation

**Windows PowerShell:**

```powershell
# Extract TASK-ID from branch name
$CURRENT_BRANCH = git branch --show-current
$TASK_ID = $CURRENT_BRANCH | Select-String -Pattern 'TASK-\d+' | ForEach-Object { $_.Matches[0].Value }
$STORY_ID = $CURRENT_BRANCH | Select-String -Pattern 'STORY-\d+' | ForEach-Object { $_.Matches[0].Value }

# Verify task file exists
if ($TASK_ID) {
    $TASK_FILE = "project/team/tasks/$TASK_ID.md"
    if (-not (Test-Path $TASK_FILE)) {
        Write-Host "❌ Task file not found: $TASK_FILE" -ForegroundColor Red
        exit 1
    }
}
```

**Unix/Linux/macOS:**

```bash
# Extract TASK-ID from branch name
CURRENT_BRANCH=$(git branch --show-current)
TASK_ID=$(echo "$CURRENT_BRANCH" | grep -oP 'TASK-\d+')
STORY_ID=$(echo "$CURRENT_BRANCH" | grep -oP 'STORY-\d+')

# Verify task file exists
if [ -n "$TASK_ID" ]; then
    TASK_FILE="project/team/tasks/$TASK_ID.md"
    if [ ! -f "$TASK_FILE" ]; then
        echo "❌ Task file not found: $TASK_FILE"
        exit 1
    fi
fi
```

### Step 2: Acceptance Criteria Verification

#### 2.1 Read Task File

**Windows PowerShell:**

```powershell
# Read the task file content
Get-Content $TASK_FILE
```

**Unix/Linux/macOS:**

```bash
# Read the task file content
cat "$TASK_FILE"
```

#### 2.2 Check Acceptance Criteria

**Windows PowerShell:**

```powershell
# Extract acceptance criteria
Get-Content $TASK_FILE | Select-String -Pattern '^- \[[ x]\]' -Context 0,0
```

**Unix/Linux/macOS:**

```bash
# Extract acceptance criteria
grep -E '^- \[[ x]\]' "$TASK_FILE"
```

- Verify ALL criteria are marked `[x]`
- Report any incomplete criteria with specific line numbers

#### 2.3 Check Definition of Done

**Windows PowerShell:**

```powershell
# Extract definition of done items
Get-Content $TASK_FILE | Select-String -Pattern '^- \[[ x]\]' -Context 0,0
```

**Unix/Linux/macOS:**

```bash
# Extract definition of done items
grep -E '^- \[[ x]\]' "$TASK_FILE"
```

- Verify ALL items are marked `[x]`
- Report any incomplete items

**If any criteria are incomplete**: List them with checkboxes and provide guidance on completion

### Step 3: Gather PR Information

#### 3.1 Extract Task Details

**Windows PowerShell:**

```powershell
# Get task title
$TASK_TITLE = (Get-Content $TASK_FILE | Select-String -Pattern '^# TASK-').Line -replace '^# ', ''

# Get story reference
$STORY_ID = (Get-Content $TASK_FILE | Select-String -Pattern 'STORY-\d+').Line | Select-Object -First 1
$STORY_FILE = "project/team/stories/$STORY_ID.md"
$STORY_TITLE = ""
if (Test-Path $STORY_FILE) {
    $STORY_TITLE = (Get-Content $STORY_FILE | Select-String -Pattern '^# STORY-').Line -replace '^# ', ''
}
```

**Unix/Linux/macOS:**

```bash
# Get task title
TASK_TITLE=$(grep '^# TASK-' "$TASK_FILE" | sed 's/^# //')

# Get story reference
STORY_ID=$(grep -oP 'STORY-\d+' "$TASK_FILE" | head -1)
STORY_FILE="project/team/stories/$STORY_ID.md"
STORY_TITLE=""
if [ -f "$STORY_FILE" ]; then
    STORY_TITLE=$(grep '^# STORY-' "$STORY_FILE" | sed 's/^# //')
fi
```

#### 3.2 Determine Base Branch and Analyze Changes

**Base branch**: If `tmp/github/progress/issue-NNN-workflow.md` exists and contains `base_branch: <branch>`, set `BASE_BRANCH=<branch>`. Otherwise `BASE_BRANCH=main`.

**Cross-platform:**

```bash
# Get changed files (use BASE_BRANCH when branch was created from non-main)
git diff --name-status origin/${BASE_BRANCH}...HEAD

# Get commit messages
git log --oneline origin/${BASE_BRANCH}...HEAD

# Get test results (from Step 1.3)
# Store the test output for inclusion in PR description
```

### Step 4: Generate AI-Enhanced PR Description

Create a comprehensive PR description using this template:

````markdown
## Task Implementation

**Task**: [TASK-XXX: {TASK_TITLE}](project/team/tasks/TASK-XXX.md)
**Story**: [STORY-XXX: {STORY_TITLE}](project/team/stories/STORY-XXX.md)

## AI-Generated Summary

{Generate 2-3 sentence summary of what was accomplished based on task description and changes}

## Implementation Details

{Analyze the changes and describe key technical decisions, new features, or improvements}

## Files Changed

### New Files

{List each new file with its purpose}

### Modified Files

{List each modified file with description of changes}

## Acceptance Criteria Status

{List all acceptance criteria with ✅ checkmarks}

## Testing Evidence

```bash
uv run pytest -m "not internet and not slow" -v
# Result: {X} passed, {Y} skipped, {Z} deselected
```
````

## Quality Checks

- ✅ All tests pass
- ✅ Code properly formatted (ruff format)
- ✅ No linting errors (ruff check)
- ✅ Documentation updated
- ✅ All acceptance criteria met

## Definition of Done

{List all DoD items with ✅ checkmarks}

## Links

- **Task**: [TASK-XXX.md](project/team/tasks/TASK-XXX.md)
- **Parent Story**: [STORY-XXX.md](project/team/stories/STORY-XXX.md)

````

### Step 5: Create PR with GitHub CLI

#### 5.1 Prepare PR Description File

**Windows PowerShell:**
```powershell
# Create temp directory
New-Item -ItemType Directory -Force -Path "tmp/github/pr-descriptions"

# Generate unique filename
$TIMESTAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$PR_FILE = "tmp/github/pr-descriptions/${TASK_ID}-${TIMESTAMP}.md"

# Save PR description to file
# {AI writes the generated description to PR_FILE}
````

**Unix/Linux/macOS:**

```bash
# Create temp directory
mkdir -p tmp/github/pr-descriptions

# Generate unique filename
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PR_FILE="tmp/github/pr-descriptions/${TASK_ID}-${TIMESTAMP}.md"

# Save PR description to file
# {AI writes the generated description to PR_FILE}
```

#### 5.2 Create Pull Request

**Cross-platform:**

```bash
# Create the PR (add --base only when BASE_BRANCH is not main)
BASE_FLAG=""
[ "$BASE_BRANCH" != "main" ] && BASE_FLAG="--base $BASE_BRANCH"
gh pr create \
  --title "$TASK_TITLE" \
  --body-file "$PR_FILE" \
  --assignee @me \
  $BASE_FLAG

# Report success
echo "✅ Pull request created successfully!"
echo "🔗 PR URL: $(gh pr view --json url --jq '.url')"
```

### Step 6: Post-Creation Actions

#### 6.1 Verify PR Creation

**Cross-platform:**

```bash
# Check PR was created
gh pr list --head "$CURRENT_BRANCH"

# Get PR number and URL
PR_NUMBER=$(gh pr list --head "$CURRENT_BRANCH" --json number --jq '.[0].number')
PR_URL=$(gh pr view "$PR_NUMBER" --json url --jq '.url')
```

#### 6.2 GitHub Actions Validation

**CRITICAL**: Verify GitHub Actions will pass before considering PR complete.

**Option A: Local Simulation (Recommended)**

```bash
# Simulate GitHub Actions locally
echo "🔍 Simulating GitHub Actions locally..."

# 1. Test dependency installation
echo "📦 Testing dependency installation..."
uv sync --dev

# 2. Test linting (matches GitHub Actions)
echo "🔍 Testing linting..."
uv run ruff check .
uv run ruff format --check .

# 3. Test unit tests (matches GitHub Actions)
echo "🧪 Testing unit tests..."
uv run pytest -m "not internet and not slow" -v

echo "✅ Local simulation complete - GitHub Actions should pass"
```

**Option B: Poll GitHub Actions (Alternative)**

```bash
# Wait for GitHub Actions to start (30 seconds)
echo "⏳ Waiting for GitHub Actions to start..."
sleep 30

# Poll GitHub Actions status
echo "🔍 Checking GitHub Actions status..."
gh run list --branch "$CURRENT_BRANCH" --limit 1

# Get run ID and check status
RUN_ID=$(gh run list --branch "$CURRENT_BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId')
if [ -n "$RUN_ID" ]; then
    echo "📊 GitHub Actions Run ID: $RUN_ID"
    echo "🔗 View at: https://github.com/$(gh repo view --json owner,name --jq '.owner.login + "/" + .name')/actions/runs/$RUN_ID"

    # Wait and check status (optional - can be done manually)
    echo "⏳ Waiting 2 minutes for initial results..."
    sleep 120
    gh run view "$RUN_ID"
fi
```

#### 6.3 Final Cleanup Validation

**CRITICAL**: Ensure no uncommitted files remain after PR creation.

```bash
# Final git status check
echo "🔍 Final cleanup validation..."
git status

# Should show: "nothing to commit, working tree clean"
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ ERROR: Uncommitted files detected after PR creation!"
    echo "Files:"
    git status --porcelain
    echo ""
    echo "All development work must be committed before creating PR."
    echo "Please commit these files and update the PR."
    exit 1
else
    echo "✅ Cleanup validation passed - no uncommitted files"
fi
```

#### 6.4 Update Local Documentation

- Update task file status if needed
- Commit any documentation updates
- Push changes

## Error Handling and Troubleshooting

### Common Issues and Solutions

#### GitHub CLI Not Authenticated

```bash
gh auth login
# Follow the prompts to authenticate
```

#### No TASK-ID in Branch Name

- Extract task information manually from commit messages
- Use branch description or recent commits to determine task
- Create minimal PR with basic information

#### Task File Not Found

- Check if task file exists in different location
- Use commit messages to infer task details
- Create PR with available information

#### Tests Failing

- List specific failed tests
- Provide debugging commands
- Suggest common fixes (imports, dependencies, etc.)

#### Uncommitted Changes

- List all uncommitted files
- Provide options: commit, stash, or discard
- Wait for user decision before proceeding

#### Linting/Formatting Issues

- Run `uv run ruff format .` to auto-fix formatting
- Provide specific linting error messages
- Suggest manual fixes for complex issues

#### GitHub Actions Python Version Issues

**Issue**: GitHub Actions using Python 3.14 (prerelease) causing dependency build failures.

**Solution**: Ensure GitHub Actions workflow specifies stable Python version:

```yaml
- name: Set up Python ${{ matrix.python-version }}
  uses: actions/setup-python@v4
  with:
    python-version: ${{ matrix.python-version }}
    allow-prereleases: false # CRITICAL: Prevent prerelease versions
```

**Common Dependency Issues**:

- `pypika` build failures with Python 3.14
- `AttributeError: module 'ast' has no attribute 'Str'` errors
- Package compatibility issues with prerelease Python versions

**Prevention**: Always test with stable Python versions (3.11, 3.12, 3.13) and avoid prerelease versions in CI/CD.

## Usage Examples

### Example 1: Standard Task PR

**Branch**: `feature/TASK-030-pandas-integration`
**Expected Output**: PR with comprehensive description of pandas integration work

### Example 2: Story PR

**Branch**: `story/STORY-008-hours-registration`
**Expected Output**: PR linking to story and all related tasks

### Example 3: Hotfix PR

**Branch**: `hotfix/HOTFIX-001-critical-bug`
**Expected Output**: PR with urgent fix description and minimal validation

## Command Invocation

When user requests PR creation:

1. **Read this command file**: `.cursor/commands/pr.md`
2. **Follow the workflow**: Execute each step in sequence
3. **Validate thoroughly**: Don't skip any validation steps
4. **Generate comprehensive description**: Use AI to enhance PR content
5. **Create PR**: Use GitHub CLI with proper parameters
6. **Report results**: Provide PR URL and summary

## Success Criteria

A successful PR creation should result in:

- ✅ All quality gates passed (tests, linting, formatting)
- ✅ All acceptance criteria verified as complete
- ✅ Comprehensive PR description with AI enhancement
- ✅ Proper linking to task/story documentation
- ✅ GitHub Actions will pass on first run
- ✅ PR is ready for review without additional work
- ✅ **Clean repository state**: No uncommitted files after PR creation
- ✅ **GitHub Actions compatibility**: Python version issues resolved
- ✅ **Local validation**: All GitHub Actions steps tested locally
- ✅ **Complete development**: All work committed and included in PR

## Notes

- This command prioritizes **first-time-right** PR creation
- Extensive validation prevents GitHub Actions failures
- AI enhancement ensures comprehensive PR descriptions
- All project standards and rules are followed
- Command is reusable for any branch/task combination
