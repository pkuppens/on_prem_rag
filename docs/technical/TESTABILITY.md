# Testability

Created: 2026-02-23
Updated: 2026-02-23

Test strategy for the API layer and data-intensive components. See [TEST_STRATEGY.md](../testing/TEST_STRATEGY.md) for full project strategy.

## Unit Tests

### API Layer

- **Mock external services**: VectorStoreManager, QASystem, LLM providers
- **Use TestClient**: FastAPI `TestClient` for route tests
- **Assert status codes, response shape**: Pydantic models validate structure

### Mocking Strategy

- Inject dependencies via FastAPI `Depends` where possible
- Use `VectorStoreManager` protocol; inject in-memory or mock implementation
- Mock LLM calls (Ollama) to avoid network in unit tests

## Integration Tests

- **API contract tests**: Verify request/response against OpenAPI schema
- **Service boundaries**: Test Routes → Services with real repositories (e.g. in-memory Chroma)
- **Mark slow/internet**: `@pytest.mark.slow`, `@pytest.mark.internet`, `@pytest.mark.ollama`

## Load Testing

### Strategy

- **When**: Before major releases; when scaling is a concern
- **Tools**: locust, k6, or artillery
- **Scenarios**: Throughput (req/s), latency (p50, p95), concurrent users

### Key Endpoints to Load Test

- `POST /api/ask` (RAG — most expensive)
- `POST /api/documents/upload`
- `POST /api/query` (retrieval-only)

### Running Load Tests

```bash
# k6 (default: 5 VUs, 30 s)
k6 run scripts/load/ask-load.js

# Locust (headless)
locust -f scripts/load/locustfile.py \
    --host=http://localhost:9180 \
    --users 5 --spawn-rate 1 --run-time 30s --headless
```

See [scripts/load/README.md](../../scripts/load/README.md) for full instructions.

### SLOs

| Endpoint | p95 | Error rate |
|----------|-----|------------|
| `GET /api/health` | < 500 ms | < 1 % |
| `POST /api/query` | < 2 000 ms | < 1 % |
| `POST /api/ask` | < 15 000 ms | < 5 % |

### Current Gaps

- No automated load tests in CI (requires Ollama; recommend manual pre-release run)

## References

- [TEST_STRATEGY.md](../testing/TEST_STRATEGY.md)
- [WRITING_TESTS.md](../testing/WRITING_TESTS.md)
- [.cursor/rules/testing.mdc](../../.cursor/rules/testing.mdc)
- [.cursor/rules/test-documentation.mdc](../../.cursor/rules/test-documentation.mdc)
