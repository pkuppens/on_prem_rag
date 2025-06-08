# Task: Create Question Answering API Endpoint

**ID**: TASK-010
**Story**: [STORY-003: Basic Q&A Interface](../stories/STORY-003.md)
**Assignee**: Backend Engineer
**Status**: Todo
**Effort**: 6 hours
**Created**: 2025-05-31
**Updated**: 2025-05-31

## Description
Implement a FastAPI endpoint `/ask` that accepts a question string and returns an answer payload. The endpoint will call the retrieval and LLM modules.

## Acceptance Criteria
- [ ] Endpoint returns HTTP 200 with JSON answer format
- [ ] Invalid input returns HTTP 400

## Dependencies
- **Blocked by**: TASK-008 (ChromaDB retrieval functions)
- **Blocks**: TASK-012

---
**Implementer**: Backend Engineer
**Reviewer**: Lead Developer
**Target Completion**: TBD
