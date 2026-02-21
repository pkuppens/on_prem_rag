---
name: code-quality-design
description: Apply complexity management, naming, and function design principles from Code Complete 2 and A Philosophy of Software Design. Use when designing modules, refactoring, or reviewing code for structural quality.
---

# Code Quality: Design and Structure

Principles from McConnell and Ousterhout. Apply by default on every generation, refactor, and review.

## Complexity Management

- **Primary goal**: Reduce complexity — anything that makes code harder to understand or modify.
- **Never add complexity for anticipated future needs.** Build what is required now.
- **Isolate complexity.** If logic is inherently complex (chunking heuristics, PII detection), contain it in one module with a simple interface. Don't leak into callers.
- **Avoid tactical programming.** Don't take shortcuts that create confusion tomorrow. If a design feels wrong, propose an alternative before implementing.

## Naming

Names are the primary documentation. A good name lets the reader skip the implementation.

- **Precise and unambiguous.** Avoid: `data`, `result`, `info`, `manager`, `handler`, `helper`, `utils`. Use: `chunked_document`, `embedding_response`, `pii_scan_result`.
- **Function names describe what they return or do**, not how: `get_relevant_chunks()` not `run_vector_search_and_filter()`.
- **Booleans** read as true/false: `is_authenticated`, `has_audit_trail`, `requires_ollama`.
- **Don't abbreviate** unless domain-standard (e.g. `rag`, `pii`, `jwt`, `llm`).
- **Consistency.** If `document` in one module, don't use `doc`, `file`, or `artifact` elsewhere for the same concept.

## Function and Module Design

- **Functions do one thing.** If you need "and" to describe it, split. Can you write a one-line docstring without "and"?
- **Deep modules, shallow interfaces.** Hide complexity behind minimal, stable interfaces. Prefer fewer, richer public functions.
- **Function length = cohesion.** 60 lines serving one purpose is fine. 10 lines doing two unrelated things is too long.
- **Limit parameters to 4 or fewer.** Use Pydantic models or dataclasses for more — matches project `models/` pattern.
- **Avoid flag parameters** (`process(doc, is_streaming=True)`). They signal a function doing two things. Split instead.
- **Files under 500 lines.** If larger, split by responsibility.
