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

## Usage Guidelines

- **Environment**: Codex does not require a local virtual environment but should be kept up to date.
- **Linting**: Allow a line length of 132 and fix whitespace issues in Python files.
- **Security**: Follow best practices and document all required environment variables.

## Conclusion

The integration of Codex aims to optimize development workflows, reduce manual coding efforts, and maintain high code quality standards. Regular updates and adherence to the outlined guidelines will ensure effective use of Codex in the project.
