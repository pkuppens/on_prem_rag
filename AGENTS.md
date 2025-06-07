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

   - Update project progress reports in markdown files like STORY-xxx, TASK-xxx, FEAT-xxx.
   - Ensure documentation is in sync with code changes.

5. **Package Management**

   - Use 'uv add -U {package}' for package installation and updates.
   - Ensure 'uv' is installed and used for managing dependencies.
   - Allow internet access for package installation to ensure all dependencies are up to date.

6. **Testing**
   - All pytests must pass, with a preference for code coverage measurements.
   - Regularly update tests to reflect code changes.

### Usage Guidelines

- **Environment**: Codex does not require a local virtual environment but should be kept up to date.
- **Linting**: Allow a line length of 132 and fix whitespace issues in Python files.
- **Security**: Follow best practices and document all required environment variables.

### Conclusion

This example implementation of Codex integration aims to optimize development workflows, reduce manual coding efforts, and maintain high code quality standards. Regular updates and adherence to the outlined guidelines will ensure effective use of Codex in the project.
