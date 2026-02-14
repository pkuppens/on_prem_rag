# Issue #77: Docker Compose Hardening — Validation Reference

**Created:** 2025-02-14 | **Updated:** 2026-02-14

Validation details, successful path commands, and acceptance criteria evidence live on **[GitHub Issue #77](https://github.com/pkuppens/on_prem_rag/issues/77)** and its comments.

## Quick links

- **Issue:** https://github.com/pkuppens/on_prem_rag/issues/77
- **Successful validation path** (PowerShell + bash): see issue comments
- **Air-gap test plan** (host disconnect + `--network none`): see issue comments
- **Port config:** `docs/PORTS.md`, `docs/TEST_DOCKER.md`, `env.example`

## Summary

| AC | Status |
|----|--------|
| AC1: Health checks | chroma, backend, auth; Ollama omitted (no curl in image) |
| AC2: Multi-stage build | `docker/backend/Dockerfile` has builder + runtime |
| AC3: Air-gapped operation | Manual: pull → disconnect → up → verify |

## References

- [ISSUE_IMPLEMENTATION_WORKFLOW.md](./ISSUE_IMPLEMENTATION_WORKFLOW.md)
- [docs/TEST_DOCKER.md](../TEST_DOCKER.md)
- [docs/DOCKER_TECHNICAL.md](../DOCKER_TECHNICAL.md)
