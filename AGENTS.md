# AGENTS.md

## Getting Started

For new agent chats working on GitHub issues: run `/get-started fix issue #N` to load the Issue Implementation Workflow into context and start with Phase 1 (Validate). See [docs/technical/AGENTS.md](docs/technical/AGENTS.md) for the full workflow summary.

## Shared Guidance

For consolidated rules see [agents/README.md](agents/README.md).

## Codex Integration Example

This document provides a practical example of how OpenAI Codex is integrated into our project to enhance productivity and streamline coding tasks.

### Workflow Integration

1. **Branch Management**

   - **Feature/Task Implementation**: MUST use feature/task branches (feature/FEAT-XXX, task/TASK-XXX)
   - **Direct to Main Allowed**: Documentation updates, CI/build configurations, agentic rules only
   - **Branch Naming**: Follow conventions in github-integration.mdc
   - Regular merges from feature branches to keep the main branch updated.

2. **Commit Strategy**

   - Use multiple commits for separate smaller tasks to maintain a clear history.
   - Ensure each commit is atomic and addresses a single concern.

3. **GitHub Actions**

   - All actions must pass, including ruff linting and fixing.
   - Adjust `pyproject.toml` to allow a permissive coding style, including a line length of 132.

4. **Documentation**

   - Use `docs/technical/DOMAIN_DRIVEN_DESIGN.md` file for architectural decisions and explanations.
   - Update project progress reports in markdown files like STORY-xxx, TASK-xxx, FEAT-xxx.
   - Ensure documentation is in sync with code changes.

5. **Package Management**

   - **CRITICAL: Always use `uv add` for project dependencies - NEVER use `pip install`**
   - Use `uv add package-name` to add runtime dependencies
   - Use `uv add --dev package-name` for development dependencies
   - Use `uv add -U {package}` for package updates
   - Ensure all imported packages exist in `pyproject.toml` dependencies
   - **Why this matters**: `pip install` only works locally but fails in fresh environments (CI/CD, containers)
   - Before importing any new package, always run `uv add package-name` first
   - Use `uv sync` to install dependencies in fresh environments
   - Allow internet access for package installation to ensure all dependencies are up to date

### Dependency Management Workflow

Before writing code that imports new packages:

1. **Check if package exists**: `grep -i "package-name" pyproject.toml`
2. **If missing, add properly**: `uv add package-name`
3. **Then write import statements**: `import package-name`
4. **Verify in fresh environment**: `uv run pytest`

**Root Cause Prevention**: The missing `httpx` dependency issue occurred because someone used `pip install httpx` locally (which worked) but didn't run `uv add httpx` to persist it in `pyproject.toml`. This caused failures in fresh environments.

6. **Testing**
   - All pytests must pass, with a preference for code coverage measurements.
   - Regularly update tests to reflect code changes.
   - Follow test documentation standards for clear business context and technical details.
   - Organize tests into classes that map to stories, features, components, or bounded contexts.
   - Provide file and class docstrings describing the scope and test goals.
   - Include functional scenarios and edge‑case unit tests within each class.

### Test Running Commands

**Default (quick tests only):**
```bash
uv run pytest                           # Runs fast tests only (excludes slow and internet)
```

**Include slow tests:**
```bash
uv run pytest -m ""                     # Run ALL tests including slow ones
uv run pytest -m "slow"                 # Run ONLY slow tests
```

**Include internet tests:**
```bash
uv run pytest --run-internet            # Include internet-dependent tests
uv run pytest -m "internet"             # Run ONLY internet tests
```

**Run everything:**
```bash
uv run pytest -m "" --run-internet      # Run ALL tests including slow and internet
```

### Test Markers

Tests use pytest markers for categorization:

| Marker | Description | Default |
|--------|-------------|---------|
| `@pytest.mark.slow` | Tests that take >5 seconds | **Skipped** |
| `@pytest.mark.internet` | Tests requiring network access | **Skipped** |
| `@pytest.mark.fts5` | Tests requiring SQLite FTS5 | Included |
| `@pytest.mark.ci_setup` | CI/CD configuration tests | Included |

**Configuration**: See `pyproject.toml` `[tool.pytest.ini_options]` for marker definitions.

### Test Documentation Standards

Based on feedback integration, all tests must include clear documentation that explains both business objectives and technical implementation:

#### Required Test Docstring Format

```python
def test_example(self):
    """As a user I want [business objective], so I can [user benefit].
    Technical: [specific technical requirement or validation approach].
    Validation: [how the test validates the requirement - optional for complex tests].
    """
```

#### Key Requirements

1. **Business Context**: Start with "As a user I want..." to explain why the test matters
2. **Technical Detail**: Include "Technical:" section explaining specific requirements
3. **Validation Method**: Add "Validation:" for complex or non-obvious test approaches
4. **User-Centric Focus**: Keep focus on user value and business outcomes

#### Examples

**Good Example:**

```python
def test_page_boundaries_are_preserved(self):
    """As a user I want search results to link to a single page, so I can quickly view and verify the result.
    Technical: Chunking should respect page boundaries - chunks must not cross from one page to another.
    Validation: Use large chunk size to force potential boundary crossing, then verify we get at least one chunk per page.
    """
```

**Bad Example:**

```python
def test_page_processing(self):
    """Test that pages are processed correctly."""  # Too vague, no business context
```

#### Benefits

- **Clear Business Context**: Developers understand why tests matter
- **Technical Clarity**: Specific requirements are documented
- **Maintenance Support**: Future developers can understand test purpose
- **Quality Assurance**: Tests are more likely to be comprehensive
- **User-Centric Development**: Keeps focus on user value

#### Enforcement

- All new tests must follow this format
- Existing tests should be updated when modified
- Code reviews should check docstring quality
- Test documentation is part of the definition of done

See [.cursor/rules/test-documentation.mdc](.cursor/rules/test-documentation.mdc) for detailed guidelines and examples.

### Bidirectional Documentation-Code References

Based on feedback integration, the following standards ensure documentation and code stay synchronized:

#### Technical Documentation Standards

1. **Code Files Section**

   - Add "## Code Files" section after "## References" in technical documentation
   - Include links to relevant code files with brief descriptions
   - For non-code documentation (e.g., AGENTS.md, CODEX.md), either omit this section or note "Intentionally left empty - no direct code dependencies"

2. **Reference Format**

   ```markdown
   ## Code Files

   - [src/rag_pipeline/core/chunking.py](src/rag_pipeline/core/chunking.py) - Main chunking implementation
   - [tests/test_chunking.py](tests/test_chunking.py) - Chunking functionality tests
   ```

#### Code File Standards

1. **Documentation Links in Docstrings**

   - Include links to relevant technical documentation in module and class docstrings
   - Use relative paths from project root
   - Example format: `See docs/technical/CHUNKING.md for detailed chunking strategies`

2. **Inline Documentation References**

   - Add documentation links in complex code sections as inline comments
   - Reference specific sections when relevant
   - Example: `# Adaptive chunking strategy - see CHUNKING.md#future-improvements`

3. **Maintenance Guidelines**
   - Update documentation links when files are moved or renamed
   - Verify links during code reviews
   - Keep documentation current with implementation changes

### Usage Guidelines

- **Environment**: Codex does not require a local virtual environment but should be kept up to date.
- **Linting**: Allow a line length of 132 and fix whitespace issues in Python files.
- **Security**: Follow best practices and document all required environment variables.

### Conclusion

This example implementation of Codex integration aims to optimize development workflows, reduce manual coding efforts, and maintain high code quality standards. Regular updates and adherence to the outlined guidelines will ensure effective use of Codex in the project.

## Task Completion and Verification

### Acceptance Criteria Tracking

When implementing tasks:

1. Mark acceptance criteria checkboxes as completed [x] when implementing each item
2. Document the implementation details in the task description or comments
3. Keep the task file updated throughout the implementation process

### Verification Process

1. Self-verification:

   - Review all acceptance criteria
   - Test each implemented feature
   - Update documentation
   - Mark completed items

2. Human verification:
   - Developer reviews the implementation
   - Verifies all acceptance criteria
   - Confirms documentation is complete
   - Updates task status

### Documentation Requirements

- Keep task files up-to-date with implementation progress
- Document any deviations from original requirements
- Include testing instructions and results
- Note any dependencies or prerequisites

## GitHub Integration and Issue Management

### Issue Management Workflow

The project uses GitHub issues integrated with the SAFe project structure for comprehensive project management:

#### Creating Issues from Project Artifacts

1. **From User Stories (STORY-\*.md)**:

   ```bash
   gh issue create --title "STORY-XXX: [Story Title]" --body-file "project/team/stories/STORY-XXX.md" --assignee @me
   ```

2. **From Tasks (TASK-\*.md)**:
   ```bash
   gh issue create --title "TASK-XXX: [Task Title]" --body-file "project/team/tasks/TASK-XXX.md" --assignee @me
   ```

#### Issue Completion and Closure

When tasks or stories are completed:

1. **Update local project files** with completed checkboxes [x]
2. **Close GitHub issues** with evidence of completion:
   ```bash
   gh issue close ISSUE_NUMBER --comment "Task completed successfully. All acceptance criteria met: ✅ [list criteria]"
   ```

### Branch Management Strategy

#### Branch Naming Conventions

- **Features**: `feature/FEAT-XXX-short-description`
- **Tasks**: `task/TASK-XXX-short-description`
- **Bugs**: `bug/BUG-XXX-short-description`
- **Hotfixes**: `hotfix/HOTFIX-XXX-short-description`

#### Branch Creation Workflow

1. **Feature Branches**:

   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/FEAT-XXX-short-description
   git push -u origin feature/FEAT-XXX-short-description
   ```

2. **Task Branches**:
   ```bash
   git checkout feature/FEAT-XXX-short-description
   git pull origin feature/FEAT-XXX-short-description
   git checkout -b task/TASK-XXX-short-description
   git push -u origin task/TASK-XXX-short-description
   ```

### Git Push Enforcement

#### Pre-Push Hook Setup

**CRITICAL**: Unit tests are automatically enforced on every git push via pre-push hooks:

```bash
# Set up the pre-push hook (run once after cloning)
uv run python scripts/setup_git_hooks.py
```

The pre-push hook will:

- Run unit tests automatically before every push
- Block pushes if tests fail
- Only run fast unit tests (excludes slow and internet-dependent tests)
- Provide clear error messages and bypass instructions

#### Emergency Bypass Option

In emergency situations only, you can bypass the pre-push hook:

```bash
# Git no-verify flag
git push --no-verify
```

**⚠️ WARNING**: This bypass should only be used in genuine emergency situations. Always fix failing tests as soon as possible.

### Pull Request Management

#### Pre-PR Requirements

**CRITICAL**: All pytest tests must pass before creating pull requests (enforced by pre-push hook):

```bash
# Run all tests locally before creating PR
uv run pytest -v

# Check code quality
uv run ruff check .
uv run ruff format --check .

# Fix formatting issues if needed
uv run ruff format .
```

#### Creating Pull Requests

```bash
# Create PR from current branch
gh pr create --title "TASK-XXX: [Task Title]" --body "Implements TASK-XXX as defined in [TASK-XXX.md](project/team/tasks/TASK-XXX.md)" --assignee @me
```

#### PR Templates

All pull requests should reference:

- Related project artifacts (STORY-_.md, TASK-_.md)
- Acceptance criteria completion status
- Testing evidence
- Documentation updates

### Quality Gates

The project enforces quality standards through GitHub Actions:

1. **Dependency Installation**: Uses `uv sync --dev` for proper dependency management
2. **Linting**: Runs `ruff check` and `ruff format --check`
3. **Testing**: Runs pytest with markers `-m "not internet and not slow"`
4. **Failure Behavior**: PRs with failing tests are automatically blocked

### Integration with SAFe Methodology

The GitHub integration maintains alignment with the existing SAFe project structure:

- **Epic → Feature → Story → Task** hierarchy preserved
- **Bidirectional synchronization** between GitHub issues and local project files
- **Acceptance criteria tracking** through checkbox completion
- **Definition of Done** verification through automated testing

See [.cursor/rules/github-integration.mdc](.cursor/rules/github-integration.mdc) for comprehensive GitHub integration guidelines and automation scripts.

## Date Formatting Standards

**CRITICAL**: Always use accurate dates in YYYY-MM-DD format. Never guess or randomly generate dates. All dates must be 100% accurate and reflect the actual system date.

### Key Requirements

1. **Use actual system date** - determine from system clock or MCP services
2. **Format as YYYY-MM-DD** - ISO 8601 standard format
3. **Never guess dates** - always use actual system date
4. **Preserve Created dates** - maintain audit history in TASK-\*.md files
5. **Update Updated dates** - reflect current system date when modifying files
6. **Ensure 100% accuracy** - dates must always reflect the actual system date

### Implementation

```python
from datetime import datetime

# Get current date in correct format
current_date = datetime.now().strftime("%Y-%m-%d")

# Use in file headers, docstrings, etc.
"""
Module description here.

Author: AI Assistant
Created: 2025-01-19  # Actual system date when created
Updated: 2025-01-19  # Current system date when last modified
"""
```

### Common Mistakes to Avoid

- ❌ `Created: 2025-01-15` (guessed date instead of actual system date)
- ❌ `Updated: 2025-01-15` (outdated when file was actually modified on 2025-10-19)
- ❌ `Date: 1/15/2025` (wrong format)
- ❌ `Date: 2025-1-5` (missing leading zeros)
- ❌ Updating existing Created dates (should preserve audit history)

See [.cursor/rules/date-formatting.mdc](.cursor/rules/date-formatting.mdc) for comprehensive date formatting guidelines.

## Related Guidance

See [agents/README.md](agents/README.md) for links to coding style, documentation style, project management and architecture rules.
