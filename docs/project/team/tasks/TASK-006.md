# Task: Implement File Ingestion Module

**ID**: TASK-006
**Story**: [STORY-002: Document Processing Pipeline](../stories/STORY-002.md)
**Assignee**: Backend Engineer
**Status**: Todo
**Effort**: 6 hours
**Created**: 2025-05-31
**Updated**: 2025-05-31

## Description
Create a module that loads PDF, DOCX, and TXT files, extracting plain text for downstream processing. Use `pypdf` and `python-docx` libraries.

## Acceptance Criteria
- [ ] Function `load_document(path)` returns extracted text for each supported format
- [ ] Errors are logged and raised for unsupported formats or corrupted files

## Dependencies
- **Blocked by**: TASK-001 (project scaffolding)
- **Blocks**: TASK-007

---
**Implementer**: Backend Engineer
**Reviewer**: Lead Developer
**Target Completion**: TBD
