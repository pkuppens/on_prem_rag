# GitHub Copilot Instructions for On-Premises RAG Project

This file provides custom instructions for GitHub Copilot to improve code reviews and suggestions for this project.

## Project Context

This is an on-premises RAG (Retrieval-Augmented Generation) application built with FastAPI, featuring document processing, embedding generation, and vector storage capabilities.

## Code Review Focus Areas

### High Priority

- **Security**: Check for potential security vulnerabilities, especially around file uploads and data handling
- **Performance**: Identify potential performance bottlenecks in document processing and embedding generation
- **Error Handling**: Ensure proper exception handling and user-friendly error messages
- **Type Safety**: Verify proper use of type hints and Pydantic models

### Medium Priority

- **Code Duplication**: Flag repeated code patterns that could be refactored
- **Import Organization**: Ensure imports are properly organized at module level
- **Documentation**: Check for missing docstrings and unclear code comments
- **Test Coverage**: Identify areas that might need additional test coverage

### Low Priority

- **Style Consistency**: Minor formatting and naming convention issues
- **Optimization**: Suggest performance improvements where appropriate

## Project-Specific Guidelines

### File Upload Security

- Always validate file types and sizes
- Check for path traversal vulnerabilities
- Ensure proper sanitization of filenames

### Document Processing

- Verify chunking strategies are appropriate for content type
- Check embedding model compatibility
- Ensure metadata preservation during processing

### API Design

- Follow RESTful conventions
- Provide clear error responses
- Include proper HTTP status codes

### Testing Standards

- Prefer integration tests over unit tests for document processing
- Mock external dependencies (embedding models, vector stores)
- Test error conditions and edge cases

## What to Ignore

- Minor style preferences that don't affect functionality
- Overly opinionated architectural suggestions
- Suggestions that would require major refactoring without clear benefits

## Review Tone

- Be constructive and specific
- Provide actionable suggestions
- Focus on code quality and maintainability
- Avoid being overly critical of working code
