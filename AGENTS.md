# AGENTS.md

## Codex Integration Example

This document provides a practical example of how OpenAI Codex is integrated into our project to enhance productivity and streamline coding tasks.

### Workflow Integration

1. **Branch Management**

   - Codex is utilized on the main branch to ensure consistency and avoid conflicts.
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
