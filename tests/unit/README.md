# Unit Tests

Fast tests with no external services. Default pytest run includes these.

**Layout** (mirrors `src/` where practical):

- `unit/core/` — chunking, document loader, embeddings (pure logic)
- `unit/api/` — route handlers (mocked dependencies)
- `unit/backend/` — backend-specific (memory, guardrails, etc.)

See [docs/testing/TEST_STRATEGY.md](../../docs/testing/TEST_STRATEGY.md).
