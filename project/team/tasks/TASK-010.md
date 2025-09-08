# Task: Create Question Answering API Endpoint

**ID**: TASK-010
**Story**: [STORY-003: Basic Q&A Interface](../stories/STORY-003.md)
**Assignee**: Backend Engineer
**Status**: Completed
**Effort**: 6 hours
**Created**: 2025-05-31
**Updated**: 2025-01-09

## Description
Implement a FastAPI endpoint `/ask` that accepts a question string and returns an answer payload. The endpoint will call the retrieval and LLM modules.

## Acceptance Criteria
- [x] Endpoint returns HTTP 200 with JSON answer format
- [x] Invalid input returns HTTP 400

## Implementation Details
- **File**: `src/backend/rag_pipeline/api/ask.py`
- **GitHub Link**: [TASK-010.md](https://github.com/pkuppens/on_prem_rag/blob/main/project/team/tasks/TASK-010.md)
- **Implementation Date**: 2025-01-09
- **Verification**: FastAPI endpoint `/api/ask` implemented with proper request/response models and error handling

## Dependencies
- **Blocked by**: TASK-008 (ChromaDB retrieval functions)
- **Blocks**: TASK-012

---
**Implementer**: Backend Engineer
**Reviewer**: Lead Developer
**Target Completion**: TBD
