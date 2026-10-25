# Update Date Tags Command: Check and Update Date Tags in Files

## Purpose

This command checks and updates date tags (`Created:` and `Updated:`) in markdown and code files according to the date-formatting rule. **Standalone**. Standards: [date-formatting.mdc](.cursor/rules/date-formatting.mdc). It ensures all files comply with the date formatting standards.

## When to Use

- After making changes to multiple files and want to ensure date tags are current
- When reviewing files for date tag compliance
- Before committing changes to ensure all date tags are accurate
- When onboarding new files that may be missing date tags
- Periodically to maintain date tag accuracy across the codebase

## Prerequisites

Before running this command, ensure:

- [ ] Python environment is set up with required dependencies
- [ ] Git is installed and accessible
- [ ] You have write access to the files being updated
- [ ] You understand which files will be modified (review the script output)

## Command Execution Workflow

### Step 1: Verify Prerequisites

#### 1.1 Check Python Environment

**Cross-platform:**

```bash
python --version
```

**Expected**: Python 3.8 or higher

#### 1.2 Check Script Exists

**Cross-platform:**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Check script exists
test -f "scripts/update_date_tags.py" && echo "✅ Script found" || echo "❌ Script not found"
```

**Windows PowerShell:**

```powershell
Test-Path "scripts/update_date_tags.py"
```

### Step 2: Run Update Script

#### 2.1 Dry Run (Recommended First)

**Cross-platform:**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Run in dry-run mode (shows what would be changed without modifying files)
python scripts/update_date_tags.py --dry-run
```

**What it does:**

- Scans all markdown and code files
- Identifies files that need date tag updates
- Shows what changes would be made
- Does NOT modify any files

**Expected Output:**

```
INFO - Scanning files for date tag compliance...
INFO - Found 150 files to check
INFO - Files needing Created tag: 5
INFO - Files needing Updated tag: 12
INFO - Files with outdated Updated tag: 8
INFO - Files already compliant: 125
INFO -
INFO - DRY RUN MODE - No files were modified
INFO - Run without --dry-run to apply changes
```

#### 2.2 Apply Updates

**Cross-platform:**

```bash
# Navigate to project root
cd "$(git rev-parse --show-toplevel)"

# Run with actual updates
python scripts/update_date_tags.py
```

**What it does:**

- Scans all markdown and code files
- Adds `Created:` tag to files missing it (with current date)
- Adds `Updated:` tag to files missing it (with current date)
- Updates `Updated:` tag in files where it's outdated (with current date)
- Preserves existing `Created:` tags (never modifies them)
- Reports summary of changes

**Expected Output:**

```
INFO - Scanning files for date tag compliance...
INFO - Current date: 2025-11-22
INFO - Found 150 files to check
INFO -
INFO - Processing files...
INFO - Added Created tag to: src/new_module.py
INFO - Added Updated tag to: docs/README.md
INFO - Updated Updated tag in: src/mcp/calendar_server.py
...
INFO -
INFO - ==================================================
INFO - UPDATE SUMMARY
INFO - ==================================================
INFO - Total files scanned: 150
INFO - Files with Created tag added: 5
INFO - Files with Updated tag added: 12
INFO - Files with Updated tag updated: 8
INFO - Files already compliant: 125
INFO - Total files modified: 25
```

### Step 3: Verify Results

#### 3.1 Check Modified Files

**Cross-platform:**

```bash
# See which files were modified
git status --short
```

**Expected**: Shows modified files with date tag updates

#### 3.2 Review Sample Changes

**Cross-platform:**

```bash
# Review changes in a sample file
git diff docs/README.md
```

**Expected Format:**

```diff
  # Project README
+
+ Created: 2025-11-22
+ Updated: 2025-11-22
```

or

```diff
  Author: AI Assistant
  Created: 2025-11-15
- Updated: 2025-11-16
+ Updated: 2025-11-22
```

#### 3.3 Validate Date Format

**Cross-platform:**

```bash
# Check a few files to ensure date format is correct
grep -r "Created:\|Updated:" src/ docs/ | head -n 10
```

**Expected Format:**

- `Created: 2025-11-22` ✅
- `Updated: 2025-11-22` ✅
- NOT `Created: 2025-11-22 10:30:45` ❌
- NOT `Created: 11/22/2025` ❌

### Step 4: Handle Edge Cases

#### 4.1 Files with Multiple Date Tags

**Issue**: Some files may have date tags in multiple locations (header and docstring)

**Solution**: The script handles this by:

- Processing files line by line
- Updating the first occurrence of each tag type
- Preserving Created tags, updating Updated tags

#### 4.2 Files with Wrong Date Format

**Issue**: Files may have dates in wrong format (e.g., `Date: 11/22/2025`)

**Solution**: The script:

- Detects common wrong formats
- Reports them in the output
- Optionally fixes them (with `--fix-format` flag)

#### 4.3 Files That Shouldn't Have Date Tags

**Issue**: Some files (like generated files, lock files) shouldn't have date tags

**Solution**: The script excludes:

- Files in `.git/`, `node_modules/`, `.venv/`, `__pycache__/`
- Binary files
- Lock files (`package-lock.json`, `poetry.lock`, etc.)
- Generated files (can be configured)

## Usage Examples

### Example 1: Standard Update

**Command:**

```bash
python scripts/update_date_tags.py
```

**Expected**: Updates all markdown and code files with current date tags

### Example 2: Dry Run First

**Command:**

```bash
python scripts/update_date_tags.py --dry-run
```

**Expected**: Shows what would be changed without modifying files

### Example 3: Update Specific Directories

**Command:**

```bash
python scripts/update_date_tags.py --include "src/ docs/"
```

**Expected**: Only processes files in `src/` and `docs/` directories

### Example 4: Exclude Specific Patterns

**Command:**

```bash
python scripts/update_date_tags.py --exclude "tests/ *.test.py"
```

**Expected**: Skips files in `tests/` directory and files matching `*.test.py`

### Example 5: Fix Wrong Date Formats

**Command:**

```bash
python scripts/update_date_tags.py --fix-format
```

**Expected**: Updates date tags and fixes wrong date formats

## Command Invocation

When user requests to update date tags:

1. **Read this command file**: `.cursor/commands/update-date-tags.md`
2. **Run dry-run first**: Execute script with `--dry-run` to preview changes
3. **Review output**: Check which files will be modified
4. **Apply updates**: Run script without `--dry-run` to apply changes
5. **Verify results**: Check git status and review sample changes
6. **Report summary**: Provide count of files updated and any issues found

## Success Criteria

A successful date tag update should result in:

- ✅ All markdown and code files have `Created:` tag (if they should have one)
- ✅ All markdown and code files have `Updated:` tag with current date
- ✅ Existing `Created:` tags are preserved (not modified)
- ✅ Date format is YYYY-MM-DD (ISO 8601)
- ✅ No files with wrong date formats remain
- ✅ Summary report shows files updated

## File Patterns

The script processes these file types:

**Markdown Files:**

- `*.md`
- `*.markdown`

**Code Files:**

- `*.py` (Python)
- `*.ts` (TypeScript)
- `*.tsx` (TypeScript React)
- `*.js` (JavaScript)
- `*.jsx` (JavaScript React)
- `*.java` (Java)
- `*.go` (Go)
- `*.rs` (Rust)
- `*.cpp`, `*.cxx`, `*.cc` (C++)
- `*.c`, `*.h` (C)
- `*.cs` (C#)

**Excluded Patterns:**

- Files in `.git/`, `node_modules/`, `.venv/`, `__pycache__/`
- Binary files
- Lock files
- Generated files (configurable)

## Date Tag Patterns

The script recognizes these date tag patterns:

**Standard Patterns:**

- `Created: YYYY-MM-DD`
- `Updated: YYYY-MM-DD`
- `Date: YYYY-MM-DD` (converted to Created/Updated)

**Common Variations (detected and reported):**

- `Created: YYYY/MM/DD` (wrong separator)
- `Created: MM/DD/YYYY` (wrong format)
- `Created: YYYY-M-D` (missing leading zeros)
- `Created: DD-MM-YYYY` (wrong order)

## Notes

- The script uses the current system date from `datetime.now()`
- Only files that are tracked by git or in specified directories are processed
- The script preserves existing `Created:` tags for audit history
- Files are processed in alphabetical order for consistent results
- The script creates backups before modifying files (optional, with `--backup` flag)
- Large files (>10MB) are skipped by default to avoid performance issues

## Related Files

- **Script**: `scripts/update_date_tags.py`
- **Rule**: `.cursor/rules/date-formatting.mdc`
- **Documentation**: `AGENTS.md` (Date Formatting Standards section)

--- End Command ---
