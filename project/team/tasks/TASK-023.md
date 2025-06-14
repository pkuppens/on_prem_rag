# Task: Upload Script for Batch Document Ingestion

**ID**: TASK-023
**Story**: [STORY-002: Document Processing Pipeline](../stories/STORY-002.md)
**Assignee**: Backend Engineer
**Status**: Completed
**Effort**: 4 hours
**Created**: 2025-06-14
**Updated**: 2025-06-14

## Description

Develop a Python CLI script that uploads multiple local documents to the existing `/api/documents/upload` endpoint. The tool should support directory recursion, filename metadata options, file type filtering, and an option to halt on errors.

## Implementation Hints

- Place the script in `scripts/upload_documents.py`
- Expose the entry point via `pyproject.toml` as `upload-documents`
- Use `httpx` for HTTP requests
- Avoid symlink loops by tracking resolved directories
- Provide detailed help text and a quiet mode for automation

## Acceptance Criteria

- [x] Script can upload single files and entire directories
- [x] `--recurse` and `--norecurse` behave as expected without following symlinks
- [x] Filename metadata stored according to `--fullpath`, `--relativepath`, or `--filenameonly`
- [x] `--filter` accepts one or more extensions (case-insensitive)
- [x] `--haltonerror` stops processing on the first failure
- [x] Unit tests cover argument parsing and upload logic

## Dependencies

- **Blocked by**: TASK-006 (File ingestion module)
- **Blocks**: None

---

**Implementer**: Backend Engineer
**Reviewer**: Lead Developer
**Target Completion**: 2025-06-14
