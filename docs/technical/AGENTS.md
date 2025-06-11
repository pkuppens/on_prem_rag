# AGENTS.md

## Introduction

This document outlines the integration and use of OpenAI Codex within our project to enhance productivity and streamline coding tasks.

## Codex Overview

OpenAI Codex is an AI system that translates natural language into code. It is designed to assist developers by providing code suggestions, automating repetitive tasks, and improving overall coding efficiency.

## Implementation Details

- **Branch Management**: Codex is used on the main branch to ensure consistency and avoid conflicts.
- **Commit Strategy**: Multiple commits are allowed for separate smaller tasks to maintain a clear history.
- **GitHub Actions**: Ensure all actions pass, including ruff linting and fixing. Some rules can be fixed automatically, while others may need adjustments in `pyproject.toml`.
- **Documentation**: Regular updates to project progress reports in markdown files like STORY-xxx, TASK-xxx, FEAT-xxx.
- **Package Management**: Use 'uv add -U {package}' for package installation and updates. Ensure 'uv' is installed and used.
- **Testing**: All pytests must pass, with a preference for code coverage measurements.

## Testing Best Practices

### Pytest Guidelines

1. **Assertion Messages**

   - Always include descriptive error messages in assertions
   - Example: `assert pages, "Expected non-empty list of pages"`

2. **Test Documentation**

   - Each test should have a docstring explaining what it verifies
   - List specific test cases and expected outcomes
   - Example:

     ```python
     """Test PDF text extraction.

     Verifies that:
     1. The function returns a non-empty list
     2. Each page is a string
     3. The list contains the expected number of pages
     """
     ```

3. **Pytest Features**

   - Use `pytest.fixture` for common test setup
   - Use `pytest.mark.parametrize` for testing multiple cases
   - Use `pytest.raises()` for testing exceptions
   - Use `pytest.approx()` for floating-point comparisons
   - Use `pytest.mark` for categorizing tests

4. **Type Checking**
   - Use `isinstance()` checks with descriptive error messages
   - Example: `assert all(isinstance(p, str) for p in pages), "All pages should be strings"`

### Pre-commit Workflow

1. **After Code Changes**

   - Run pre-commit hooks to fix formatting issues
   - Commands:
     ```bash
     pre-commit run ruff
     pre-commit run ruff-format
     ```
   - This ensures consistent code style across the project

2. **Common Fixes**
   - Code formatting (ruff-format)
   - Linting and auto-fixing (ruff)
   - Import sorting (ruff)
   - Type checking (ruff)

## Usage Guidelines

- **Environment**: Codex does not require a local virtual environment but should be kept up to date.
- **Linting**: Allow a line length of 132 and fix whitespace issues in Python files.
- **Security**: Follow best practices and document all required environment variables.

## Conclusion

The integration of Codex aims to optimize development workflows, reduce manual coding efforts, and maintain high code quality standards. Regular updates and adherence to the outlined guidelines will ensure effective use of Codex in the project.
